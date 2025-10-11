from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from .models import Duty, DutySchedule, MonthlyDutyPlan
from unit.models import Faculty, Department
import calendar
from collections import defaultdict
import re

class DutyDistributionService:
    def __init__(self, month):
        self.month = month
        self.year = month.year
        self.month_num = month.month
        self.days_in_month = calendar.monthrange(self.year, self.month_num)[1]
        
    def get_available_units(self):
        """Получить все доступные подразделения для распределения"""
        faculties = Faculty.objects.all()
        departments_without_faculty = Department.objects.filter(faculty__isnull=True)
        
        units = []
        for faculty in faculties:
            units.append({
                'type': 'faculty',
                'id': faculty.id,
                'name': faculty.name,
                'object': faculty
            })
        
        for department in departments_without_faculty:
            units.append({
                'type': 'department', 
                'id': department.id,
                'name': department.name,
                'object': department
            })
            
        return units
    
    def get_fixed_duties(self, duties):
        """Получить наряды с фиксированным закреплением"""
        fixed_duties = []
        for duty in duties:
            if duty.assigned_faculty:
                fixed_duties.append({
                    'duty': duty,
                    'unit_type': 'faculty',
                    'unit': duty.assigned_faculty,
                    'unit_name': duty.assigned_faculty.name
                })
            elif duty.assigned_department:
                fixed_duties.append({
                    'duty': duty,
                    'unit_type': 'department', 
                    'unit': duty.assigned_department,
                    'unit_name': duty.assigned_department.name
                })
        return fixed_duties
    
    def parse_date_range(self, range_str):
        """Парсинг диапазона дат из строки"""
        try:
            # Пробуем разные разделители
            separators = [' to ', ' — ', ' - ', ' по ']
            dates = None
            for sep in separators:
                if sep in range_str:
                    dates = range_str.split(sep)
                    break
            
            if not dates:
                # Пробуем разделить по пробелам
                dates = range_str.split()
            
            if len(dates) == 2:
                start_str = dates[0].strip()
                end_str = dates[1].strip()
                
                print(f"Parsing date range: '{start_str}' to '{end_str}'")  # Debug
                
                # Пробуем разные форматы дат
                for fmt in ['%d.%m.%Y', '%d.%m.%y']:
                    try:
                        start_date = datetime.strptime(start_str, fmt).date()
                        end_date = datetime.strptime(end_str, fmt).date()
                        print(f"Successfully parsed: {start_date} to {end_date}")  # Debug
                        return start_date, end_date
                    except ValueError:
                        continue
                        
        except (ValueError, IndexError, AttributeError) as e:
            print(f"Error parsing date range '{range_str}': {e}")
            
        return None, None
    
    def parse_specific_date(self, date_str):
        """Парсинг конкретной даты"""
        for fmt in ['%d.%m.%Y', '%d.%m.%y']:
            try:
                date = datetime.strptime(date_str.strip(), fmt).date()
                print(f"Successfully parsed specific date: {date}")  # Debug
                return date
            except ValueError:
                continue
        print(f"Failed to parse specific date: {date_str}")  # Debug
        return None
    
    def should_schedule_duty(self, duty, date, weekday, duty_schedule_settings):
        """Определить, должен ли наряд быть в указанный день"""
        duty_settings = duty_schedule_settings.get(str(duty.id), {})
        
        ranges = duty_settings.get('ranges', [])
        specific_dates = duty_settings.get('specific_dates', [])
        weekdays = duty_settings.get('weekdays', [])
        
        print(f"Checking duty {duty.duty_name} for date {date}")  # Debug
        print(f"Settings - ranges: {ranges}, specific_dates: {specific_dates}, weekdays: {weekdays}")  # Debug
        
        # Если нет никаких настроек - наряд на весь месяц
        if not ranges and not specific_dates and not weekdays:
            print("No settings - scheduling for entire month")  # Debug
            return True
        
        date_scheduled = False
        
        # Проверяем диапазоны дат
        for range_str in ranges:
            start_date, end_date = self.parse_date_range(range_str)
            if start_date and end_date:
                print(f"Checking range {start_date} - {end_date} against {date}")  # Debug
                if start_date <= date <= end_date:
                    print("Date falls within range")  # Debug
                    date_scheduled = True
                    break
            else:
                print(f"Failed to parse range: {range_str}")  # Debug
        
        # Проверяем конкретные даты
        if not date_scheduled and specific_dates:
            for date_str in specific_dates:
                specific_date = self.parse_specific_date(date_str)
                if specific_date and specific_date == date:
                    print(f"Date matches specific date: {specific_date}")  # Debug
                    date_scheduled = True
                    break
        
        # Проверяем дни недели
        if not date_scheduled and weekdays:
            weekday_names = {
                0: 'Понедельник', 
                1: 'Вторник', 
                2: 'Среда', 
                3: 'Четверг',
                4: 'Пятница', 
                5: 'Суббота', 
                6: 'Воскресенье'
            }
            current_weekday_name = weekday_names.get(weekday)
            
            print(f"Current weekday: {current_weekday_name} ({weekday})")  # Debug
            print(f"Configured weekdays: {weekdays}")  # Debug
            
            for day_setting in weekdays:
                # Если настройка - число
                if isinstance(day_setting, int) and day_setting == weekday:
                    print(f"Matched by number: {day_setting}")  # Debug
                    date_scheduled = True
                    break
                # Если настройка - строка (название дня)
                elif isinstance(day_setting, str):
                    # Проверяем название дня
                    if day_setting == current_weekday_name:
                        print(f"Matched by name: {day_setting}")  # Debug
                        date_scheduled = True
                        break
                    # Проверяем число как строку
                    elif day_setting.isdigit() and int(day_setting) == weekday:
                        print(f"Matched by string number: {day_setting}")  # Debug
                        date_scheduled = True
                        break
        
        print(f"Final decision for {date}: {date_scheduled}")  # Debug
        return date_scheduled
    
    def distribute_duties_improved(self, duties, monthly_plan):
        units = self.get_available_units()
        fixed_duties = self.get_fixed_duties(duties)
        
        schedules = []
        
        # Получаем настройки расписания для каждого наряда
        duty_schedule_settings = monthly_plan.duty_schedule_settings
        
        print(f"Starting distribution for {len(duties)} duties")  # Debug
        print(f"Schedule settings: {duty_schedule_settings}")  # Debug
        
        # Считаем текущую нагрузку на подразделения
        unit_load = {unit['id']: 0 for unit in units}
        
        # Создаем список всех дней месяца
        month_days = [datetime(self.year, self.month_num, day).date() 
                     for day in range(1, self.days_in_month + 1)]
        
        total_scheduled = 0
        
        # Сначала распределяем фиксированные наряды
        for date in month_days:
            weekday = date.weekday()
            
            for fixed in fixed_duties:
                if self.should_schedule_duty(fixed['duty'], date, weekday, duty_schedule_settings):
                    schedule = DutySchedule(
                        duty=fixed['duty'],
                        date=date,
                        assigned_unit_type=fixed['unit_type']
                    )
                    if fixed['unit_type'] == 'faculty':
                        schedule.assigned_faculty = fixed['unit']
                        unit_load[fixed['unit'].id] += 1
                    else:
                        schedule.assigned_department = fixed['unit']
                        unit_load[fixed['unit'].id] += 1
                    schedules.append(schedule)
                    total_scheduled += 1
        
        # Затем распределяем остальные наряды
        remaining_duties = [d for d in duties if d not in [fd['duty'] for fd in fixed_duties]]
        
        print(f"Remaining duties to distribute: {len(remaining_duties)}")  # Debug
        
        for date in month_days:
            weekday = date.weekday()
            
            for duty in remaining_duties:
                if self.should_schedule_duty(duty, date, weekday, duty_schedule_settings):
                    # Выбираем подразделение с минимальной текущей нагрузкой
                    min_load = min(unit_load.values())
                    available_units = [u for u in units if unit_load[u['id']] == min_load]
                    min_load_unit = available_units[0] if available_units else units[0]
                    
                    schedule = DutySchedule(
                        duty=duty,
                        date=date,
                        assigned_unit_type=min_load_unit['type']
                    )
                    if min_load_unit['type'] == 'faculty':
                        schedule.assigned_faculty = min_load_unit['object']
                    else:
                        schedule.assigned_department = min_load_unit['object']
                    
                    schedules.append(schedule)
                    unit_load[min_load_unit['id']] += 1
                    total_scheduled += 1
        
        print(f"Total schedules created: {total_scheduled}")  # Debug
        return schedules

    @transaction.atomic
    def generate_schedule(self, monthly_plan):
        """Сгенерировать полное расписание"""
        print(f"Generating schedule for {monthly_plan.month}")  # Debug
        
        # Удаляем старое расписание для этого месяца
        deleted_count = DutySchedule.objects.filter(
            date__year=self.year,
            date__month=self.month_num
        ).delete()
        
        print(f"Deleted {deleted_count} old schedules")  # Debug
        
        # Генерируем новое расписание
        duties = monthly_plan.duties.all()
        print(f"Planning for duties: {[d.duty_name for d in duties]}")  # Debug
        
        schedules = self.distribute_duties_improved(duties, monthly_plan)
        
        print(f"Created {len(schedules)} schedule entries")  # Debug
        
        # Сохраняем в базу
        if schedules:
            DutySchedule.objects.bulk_create(schedules)
            print(f"Successfully saved {len(schedules)} schedules to database")  # Debug
        else:
            print("No schedules to save")  # Debug
        
        # Помечаем план как сгенерированный
        monthly_plan.is_generated = True
        monthly_plan.last_generated_at = timezone.now()
        monthly_plan.save()
        
        print(f"Generation complete. Return count: {len(schedules)}")  # Debug
        return len(schedules)