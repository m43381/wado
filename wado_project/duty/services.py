from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from .models import Duty, DutySchedule, MonthlyDutyPlan
from unit.models import Faculty, Department
import calendar
from collections import defaultdict
import re
from .utils import normalize_weekday_setting

class DutyDistributionService:
    def __init__(self, month):
        self.month = month
        self.year = month.year
        self.month_num = month.month
        self.days_in_month = calendar.monthrange(self.year, self.month_num)[1]
        
    def get_available_units(self, selected_units):
        """Получить выбранные подразделения для распределения"""
        faculties = []
        departments = []
        
        for unit in selected_units:
            if unit.startswith('faculty_'):
                faculty_id = int(unit.replace('faculty_', ''))
                try:
                    faculty = Faculty.objects.get(id=faculty_id)
                    faculties.append(faculty)
                except Faculty.DoesNotExist:
                    continue
            elif unit.startswith('department_'):
                dept_id = int(unit.replace('department_', ''))
                try:
                    department = Department.objects.get(id=dept_id)
                    departments.append(department)
                except Department.DoesNotExist:
                    continue
        
        return faculties, departments
    
    def get_fixed_duties(self, duties, selected_units):
        """Получить наряды с фиксированным закреплением"""
        fixed_duties = []
        for duty in duties:
            if duty.assigned_faculty or duty.assigned_department:
                unit_type = 'faculty' if duty.assigned_faculty else 'department'
                unit = duty.assigned_faculty or duty.assigned_department
                unit_id = f"{unit_type}_{unit.id}"
                
                # Проверяем, выбрано ли закрепленное подразделение
                if unit_id in selected_units:
                    fixed_duties.append({
                        'duty': duty,
                        'unit_type': unit_type,
                        'unit': unit,
                        'unit_name': unit.name,
                        'is_fixed': True
                    })
                else:
                    # Если фиксированное подразделение не выбрано, наряд становится ротационным
                    fixed_duties.append({
                        'duty': duty,
                        'unit_type': None,
                        'unit': None,
                        'unit_name': None,
                        'is_fixed': False
                    })
            else:
                # Обычный ротационный наряд
                fixed_duties.append({
                    'duty': duty,
                    'unit_type': None,
                    'unit': None,
                    'unit_name': None,
                    'is_fixed': False
                })
        
        return fixed_duties
    
    def parse_date_range(self, range_str):
        """Парсинг диапазона дат из строки"""
        try:
            print(f"🔍 Парсинг диапазона: '{range_str}'")
            
            # Основные разделители
            separators = [' по ', ' to ', ' — ', ' - ']
            
            for sep in separators:
                if sep in range_str:
                    dates = range_str.split(sep)
                    if len(dates) == 2:
                        start_str = dates[0].strip()
                        end_str = dates[1].strip()
                        
                        print(f"   Начало: '{start_str}', Конец: '{end_str}'")
                        
                        # Очищаем от лишних символов
                        start_clean = re.sub(r'[^\d.]', '', start_str)
                        end_clean = re.sub(r'[^\d.]', '', end_str)
                        
                        # Пробуем разные форматы
                        for fmt in ['%d.%m.%Y', '%d.%m.%y']:
                            try:
                                start_date = datetime.strptime(start_clean, fmt).date()
                                end_date = datetime.strptime(end_clean, fmt).date()
                                print(f"   ✅ Успешно распарсено: {start_date} - {end_date}")
                                return start_date, end_date
                            except ValueError:
                                continue
                    
            print(f"❌ Не удалось распарсить диапазон: '{range_str}'")
            return None, None
            
        except Exception as e:
            print(f"❌ Ошибка парсинга диапазона '{range_str}': {e}")
            return None, None
    
    def parse_specific_date(self, date_str):
        """Парсинг конкретной даты с улучшенной обработкой"""
        if not date_str or not isinstance(date_str, str):
            return None
        
        # Очищаем строку от лишних пробелов
        clean_date = date_str.strip()
        
        print(f"   🔍 Парсинг конкретной даты: '{clean_date}'")
        
        for fmt in ['%d.%m.%Y', '%d.%m.%y']:
            try:
                date = datetime.strptime(clean_date, fmt).date()
                print(f"     ✅ Успешно распарсено: {date}")
                return date
            except ValueError as e:
                print(f"     ❌ Ошибка формата {fmt}: {e}")
                continue
        
        print(f"     ❌ Не удалось распарсить дату: '{clean_date}'")
        return None
    
    def validate_date_range_format(self, range_str):
        """Проверка формата диапазона дат"""
        pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})\s+(?:по|to|—|-)\s+(\d{1,2}\.\d{1,2}\.\d{4})'
        return bool(re.match(pattern, range_str))
    

    def should_schedule_duty(self, duty, date, weekday, duty_schedule_settings):
        """Определить, должен ли наряд быть в указанный день с учетом всех настроек"""
        duty_settings = duty_schedule_settings.get(str(duty.id), {})
        
        ranges = duty_settings.get('ranges', [])
        specific_dates = duty_settings.get('specific_dates', [])
        weekdays = duty_settings.get('weekdays', [])
        
        # Если нет никаких настроек - наряд на весь месяц
        if not ranges and not specific_dates and not weekdays:
            return True
        
        # Проверяем конкретные даты (высший приоритет)
        if specific_dates:
            for date_str in specific_dates:
                specific_date = self.parse_specific_date(date_str)
                if specific_date and specific_date == date:
                    return True
        
        # Проверяем диапазоны дат
        date_in_range = False
        for range_str in ranges:
            # Пропускаем некорректные форматы
            if not self.validate_date_range_format(range_str):
                print(f"⚠️ Пропускаем некорректный диапазон: {range_str}")
                continue
                
            start_date, end_date = self.parse_date_range(range_str)
            if start_date and end_date:
                if start_date <= date <= end_date:
                    date_in_range = True
                    break
        
        # Проверяем дни недели
        weekday_match = False
        if weekdays:
            for day_setting in weekdays:
                normalized_weekday = normalize_weekday_setting(day_setting)
                if normalized_weekday is not None and normalized_weekday == weekday:
                    weekday_match = True
                    break
        
        # Комбинируем условия: если есть диапазон ИЛИ дни недели
        return date_in_range or weekday_match
    
    def get_duty_schedule_dates(self, duty, duty_schedule_settings):
        """Получить все даты, когда должен быть наряд - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        dates = []
        duty_settings = duty_schedule_settings.get(str(duty.id), {})
        
        print(f"\n📅 Получение дат для наряда {duty.duty_name}:")
        print(f"   Настройки: {duty_settings}")
        
        # Если нет никаких настроек - наряд на весь месяц
        if not duty_settings.get('ranges') and not duty_settings.get('specific_dates') and not duty_settings.get('weekdays'):
            print("   - Нет настроек, используем весь месяц")
            for day in range(1, self.days_in_month + 1):
                date = datetime(self.year, self.month_num, day).date()
                dates.append(date)
            return dates
        
        # Собираем ВСЕ возможные даты из всех условий
        all_possible_dates = set()
        
        # 1. Обрабатываем конкретные даты
        specific_dates = duty_settings.get('specific_dates', [])
        if specific_dates:
            print(f"   - Обработка {len(specific_dates)} конкретных дат: {specific_dates}")
            for date_str in specific_dates:
                specific_date = self.parse_specific_date(date_str)
                if specific_date:
                    all_possible_dates.add(specific_date)
                    print(f"     ✅ Добавлена конкретная дата: {specific_date}")
        
        # 2. Обрабатываем диапазоны дат
        ranges = duty_settings.get('ranges', [])
        if ranges:
            print(f"   - Обработка {len(ranges)} диапазонов")
            for range_str in ranges:
                start_date, end_date = self.parse_date_range(range_str)
                if start_date and end_date:
                    print(f"     📆 Диапазон: {start_date} - {end_date}")
                    current_date = start_date
                    while current_date <= end_date:
                        all_possible_dates.add(current_date)
                        current_date += timedelta(days=1)
        
        # 3. Обрабатываем дни недели - ВАЖНОЕ ИСПРАВЛЕНИЕ
        weekdays = duty_settings.get('weekdays', [])
        if weekdays:
            print(f"   - Обработка {len(weekdays)} дней недели: {weekdays}")
            
            # Создаем множество для быстрой проверки
            target_weekdays = set()
            for day_setting in weekdays:
                normalized_weekday = normalize_weekday_setting(day_setting)
                if normalized_weekday is not None:
                    target_weekdays.add(normalized_weekday)
                    print(f"     📋 Целевой день недели: {normalized_weekday} ({day_setting})")
                else:
                    print(f"     ❌ Не удалось нормализовать день недели: {day_setting}")
            
            print(f"   - Целевые дни недели (числа): {target_weekdays}")
            
            # Проходим по всем дням месяца и добавляем те, что соответствуют дням недели
            for day in range(1, self.days_in_month + 1):
                date = datetime(self.year, self.month_num, day).date()
                weekday = date.weekday()
                
                if weekday in target_weekdays:
                    all_possible_dates.add(date)
                    print(f"     ✅ Добавлен день недели: {date} (день недели {weekday})")
        
        # Преобразуем обратно в список и сортируем
        dates = sorted(list(all_possible_dates))
        print(f"   📊 Итого дат для наряда: {len(dates)}")
        
        return dates

    
    def distribute_duties_improved(self, duties, monthly_plan):
        """Улучшенное распределение нарядов с учетом всех условий"""
        selected_units = monthly_plan.selected_units or []
        faculties, departments = self.get_available_units(selected_units)
        fixed_duties = self.get_fixed_duties(duties, selected_units)
        
        schedules = []
        
        # Получаем настройки расписания для каждого наряда
        duty_schedule_settings = monthly_plan.duty_schedule_settings
        
        # Создаем список всех доступных подразделений для ротации
        rotation_units = []
        for faculty in faculties:
            rotation_units.append({
                'type': 'faculty',
                'object': faculty,
                'id': f"faculty_{faculty.id}",
                'name': f"Факультет {faculty.name}"
            })
        for department in departments:
            rotation_units.append({
                'type': 'department', 
                'object': department,
                'id': f"department_{department.id}",
                'name': f"Кафедра {department.name}"
            })
        
        if not rotation_units:
            print("❌ Нет доступных подразделений для распределения")
            return schedules
        
        print(f"✅ Доступно подразделений: {len(rotation_units)}")
        
        # Считаем текущую нагрузку на подразделения
        unit_load = {unit['id']: 0 for unit in rotation_units}
        
        # Распределяем все наряды
        for duty_info in fixed_duties:
            duty = duty_info['duty']
            
            # Получаем даты для этого наряда
            duty_dates = self.get_duty_schedule_dates(duty, duty_schedule_settings)
            
            if not duty_dates:
                print(f"⚠️ Для наряда {duty.duty_name} нет подходящих дат")
                continue
            
            print(f"🎯 Наряд {duty.duty_name} на {len(duty_dates)} дней")
            
            if duty_info['is_fixed'] and duty_info['unit']:
                # Фиксированный наряд для выбранного подразделения
                unit = duty_info['unit']
                unit_type = duty_info['unit_type']
                unit_id = f"{unit_type}_{unit.id}"
                
                print(f"   📌 Фиксированно за: {unit.name}")
                
                for date in duty_dates:
                    schedule = DutySchedule(
                        duty=duty,
                        date=date,
                        assigned_unit_type=unit_type,
                        is_manually_assigned=False  # Автоматическое распределение
                    )
                    if unit_type == 'faculty':
                        schedule.assigned_faculty = unit
                    else:
                        schedule.assigned_department = unit
                    
                    schedules.append(schedule)
                    unit_load[unit_id] += 1
                    
            else:
                # Ротационный наряд (включая фиксированные наряды с неподходящими подразделениями)
                print(f"   🔄 Ротационный наряд")
                
                for i, date in enumerate(duty_dates):
                    # Выбираем подразделение с минимальной текущей нагрузкой
                    min_load = min(unit_load.values())
                    available_units = [u for u in rotation_units if unit_load[u['id']] == min_load]
                    
                    if not available_units:
                        available_units = rotation_units
                    
                    # Для равномерного распределения используем индекс дня
                    day_index = i % len(available_units)
                    selected_unit = available_units[day_index]
                    
                    schedule = DutySchedule(
                        duty=duty,
                        date=date,
                        assigned_unit_type=selected_unit['type'],
                        is_manually_assigned=False  # Автоматическое распределение
                    )
                    if selected_unit['type'] == 'faculty':
                        schedule.assigned_faculty = selected_unit['object']
                    else:
                        schedule.assigned_department = selected_unit['object']
                    
                    schedules.append(schedule)
                    unit_load[selected_unit['id']] += 1
        
        # Выводим статистику распределения
        print("\n=== СТАТИСТИКА РАСПРЕДЕЛЕНИЯ ===")
        total_schedules = 0
        for unit in rotation_units:
            print(f"📊 {unit['name']}: {unit_load[unit['id']]} нарядов")
            total_schedules += unit_load[unit['id']]
        print(f"📈 Всего распределено: {len(schedules)} нарядов")
        
        return schedules
    
    def generate_schedule(self, monthly_plan):
        """Сгенерировать полное расписание"""
        print(f"\n🎯 ГЕНЕРАЦИЯ РАСПИСАНИЯ НА {monthly_plan.month.strftime('%B %Y')} 🎯")
        
        try:
            # Удаляем старое расписание для этого месяца
            deleted_count, _ = DutySchedule.objects.filter(
                date__year=self.year,
                date__month=self.month_num
            ).delete()
            
            print(f"🗑️ Удалено старых записей: {deleted_count}")
            
            # Генерируем новое расписание
            duties = monthly_plan.duties.all()
            print(f"📋 Нарядов для планирования: {len(duties)}")
            print(f"🏢 Выбранные подразделения: {monthly_plan.selected_units}")
            
            schedules = self.distribute_duties_improved(duties, monthly_plan)
            
            print(f"✅ Создано новых записей: {len(schedules)}")
            
            # Сохраняем в базу
            if schedules:
                DutySchedule.objects.bulk_create(schedules)
                print(f"💾 Успешно сохранено в базу данных")
            else:
                print("⚠️ Нет расписаний для сохранения")
            
            # ВАЖНО: Помечаем план как сгенерированный и СОХРАНЯЕМ
            monthly_plan.is_generated = True
            monthly_plan.last_generated_at = timezone.now()
            monthly_plan.save(update_fields=['is_generated', 'last_generated_at'])
            
            print(f"✅ План помечен как сгенерированный: is_generated={monthly_plan.is_generated}")
            print("🎉 Генерация завершена успешно!")
            
            return len(schedules)
            
        except Exception as e:
            print(f"❌ Ошибка в generate_schedule: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0