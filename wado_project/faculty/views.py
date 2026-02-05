# faculty/views.py - ИСПРАВЛЕННЫЙ
from django.views.generic import TemplateView, View, DetailView, ListView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, Case, When, Value, BooleanField
import calendar
from collections import defaultdict
import json

from core.mixins import HasFacultyMixin
from people.models import People
from unit.models import Department, Faculty
from duty.models import Duty, DutySchedule, MonthlyDutyPlan
from missing.models import DepartmentMissing, FacultyMissing
from permission.models import DepartmentDutyPermission
from duty.utils import normalize_weekday_setting

# Импортируем модель из models.py
from .models import FacultyMonthlyPlan


# ==================== SERVICES ====================

class FacultyDistributionService:
    """Сервис для генерации расписания факультетских нарядов"""
    
    def __init__(self, faculty, month_date):
        self.faculty = faculty
        self.month_date = month_date
        self.year = month_date.year
        self.month = month_date.month
    
    def generate_schedule(self, faculty_plan):
        """Сгенерировать расписание факультетских нарядов"""
        
        # Получаем выбранные наряды
        duties = Duty.objects.filter(
            faculty=self.faculty,
            department__isnull=True,
            is_commandant=False
        )
        
        # Если план существует, фильтруем по выбранным нарядам
        if faculty_plan.duty_schedule_settings:
            duty_ids = [int(duty_id) for duty_id in faculty_plan.duty_schedule_settings.keys()]
            duties = duties.filter(id__in=duty_ids)
            print(f"📋 Настройки плана: {faculty_plan.duty_schedule_settings}")
            print(f"📋 Ключи настроек: {list(faculty_plan.duty_schedule_settings.keys())}")
        
        # Получаем выбранные подразделения
        selected_units = faculty_plan.selected_units
        if not selected_units:
            selected_units = ['management']  # По умолчанию - только управление
        
        # Собираем все дни месяца, когда должны быть наряды
        schedule_days = self._get_schedule_days(faculty_plan, duties)
        
        # Выводим отладку по дням для каждого наряда
        for duty, dates in schedule_days.items():
            print(f"📅 Наряд '{duty.duty_name}' имеет {len(dates)} дней расписания")
            if len(dates) > 0:
                print(f"  Первые 10 дней: {dates[:10]}")
        
        # Сначала удаляем старые записи для этого месяца
        deleted_count = DutySchedule.objects.filter(
            duty__in=duties,
            date__year=self.year,
            date__month=self.month,
            is_manually_assigned=False
        ).delete()[0]
        print(f"🗑️ Удалено {deleted_count} старых записей")
        
        # Распределяем наряды по подразделениям
        created_count = 0
        for duty, dates in schedule_days.items():
            for date in dates:
                # Выбираем подразделение для этого дня
                assigned_unit = self._select_unit_for_day(
                    date, duty, selected_units, faculty_plan
                )
                
                # Создаем расписание
                if self._create_duty_schedule(
                    duty, date, assigned_unit, faculty_plan
                ):
                    created_count += 1
        
        # Обновляем план
        faculty_plan.is_generated = True
        faculty_plan.last_generated_at = timezone.now()
        faculty_plan.save()
        
        return created_count
    
    def _get_schedule_days(self, faculty_plan, duties):
        """Получить дни месяца для каждого наряда"""
        schedule_days = defaultdict(list)
        
        # Получаем все дни месяца
        cal = calendar.Calendar(firstweekday=0)
        month_days = [
            d for d in cal.itermonthdates(self.year, self.month)
            if d.month == self.month
        ]
        
        for duty in duties:
            # Получаем настройки расписания для наряда
            schedule_data = faculty_plan.get_duty_schedule(duty)
            
            print(f"🔍 Получены настройки для наряда {duty.id} ({duty.duty_name}):")
            print(f"   Данные: {schedule_data}")
            print(f"   Тип данных: {type(schedule_data)}")
            
            # Если нет настроек - наряд на весь месяц каждый день
            if not schedule_data or not any(schedule_data.values()):
                schedule_days[duty] = month_days
                print(f"   ⚠️ Нет настроек, используем весь месяц")
                continue
            
            # Применяем настройки
            days_for_duty = self._apply_schedule_settings(
                month_days, schedule_data, duty.id
            )
            schedule_days[duty] = days_for_duty
        
        return schedule_days
    
    def _apply_schedule_settings(self, month_days, schedule_data, duty_id=None):
        """Применить настройки расписания к дням месяца - ИЛИ логика"""
        result_days = []
        
        print(f"⚙️ Применение настроек расписания (duty_id={duty_id}):")
        print(f"  - Диапазоны: {schedule_data.get('ranges', [])}")
        print(f"  - Конкретные даты: {schedule_data.get('specific_dates', [])}")
        print(f"  - Дни недели: {schedule_data.get('weekdays', [])}")
        
        # Нормализуем дни недели
        weekdays = schedule_data.get('weekdays', [])
        normalized_weekdays = []
        
        for day_setting in weekdays:
            if isinstance(day_setting, str):
                if day_setting.isdigit():
                    normalized_weekdays.append(int(day_setting))
                else:
                    weekday_map = {
                        'понедельник': 0, 'пн': 0,
                        'вторник': 1, 'вт': 1,
                        'среда': 2, 'ср': 2,
                        'четверг': 3, 'чт': 3,
                        'пятница': 4, 'пт': 4,
                        'суббота': 5, 'сб': 5,
                        'воскресенье': 6, 'вс': 6
                    }
                    day_lower = day_setting.lower()
                    if day_lower in weekday_map:
                        normalized_weekdays.append(weekday_map[day_lower])
            elif isinstance(day_setting, int):
                normalized_weekdays.append(day_setting)
        
        print(f"  - Нормализованные дни недели: {normalized_weekdays}")
        
        # Преобразуем конкретные даты из строк в объекты даты
        specific_dates = []
        for date_str in schedule_data.get('specific_dates', []):
            try:
                date_obj = datetime.strptime(date_str.strip(), '%d.%m.%Y').date()
                specific_dates.append(date_obj)
            except Exception as e:
                print(f"⚠️ Ошибка при разборе даты {date_str}: {e}")
        
        # Получаем диапазоны дат
        date_ranges = []
        for range_str in schedule_data.get('ranges', []):
            try:
                if ' по ' in range_str:
                    start_str, end_str = range_str.split(' по ')
                    start_date = datetime.strptime(start_str.strip(), '%d.%m.%Y').date()
                    end_date = datetime.strptime(end_str.strip(), '%d.%m.%Y').date()
                    date_ranges.append((start_date, end_date))
            except Exception as e:
                print(f"⚠️ Ошибка при разборе диапазона {range_str}: {e}")
        
        print(f"  - Диапазоны (объекты): {date_ranges}")
        print(f"  - Конкретные даты (объекты): {specific_dates}")
        
        # ИЛИ логика: день должен соответствовать ХОТЯ БЫ ОДНОМУ условию
        for day in month_days:
            day_added = False
            
            # Условие 1: день в диапазоне?
            if date_ranges and not day_added:
                for start_date, end_date in date_ranges:
                    if start_date <= day <= end_date:
                        result_days.append(day)
                        day_added = True
                        break
            
            # Условие 2: конкретная дата?
            if specific_dates and not day_added:
                if day in specific_dates:
                    result_days.append(day)
                    day_added = True
            
            # Условие 3: день недели?
            if normalized_weekdays and not day_added:
                if day.weekday() in normalized_weekdays:
                    result_days.append(day)
                    day_added = True
            
            # Если нет ни одного условия - день не добавляется
            if not day_added:
                # Проверяем, есть ли вообще какие-то условия
                has_conditions = (date_ranges or specific_dates or normalized_weekdays)
                # Если нет ни одного условия - добавляем ВСЕ дни (по умолчанию)
                if not has_conditions:
                    result_days.append(day)
        
        # Убираем дубликаты (если день попал под несколько условий)
        unique_days = list(set(result_days))
        unique_days.sort()
        
        print(f"✅ Найдено {len(unique_days)} уникальных дней по настройкам")
        
        return unique_days
    
    def _is_in_range(self, day, range_str):
        """Проверить, находится ли день в диапазоне"""
        try:
            if ' по ' in range_str:
                start_str, end_str = range_str.split(' по ')
                start_date = datetime.strptime(start_str.strip(), '%d.%m.%Y').date()
                end_date = datetime.strptime(end_str.strip(), '%d.%m.%Y').date()
                return start_date <= day <= end_date
        except Exception as e:
            print(f"❌ Ошибка при проверке диапазона {range_str}: {e}")
        return False
    
    def _select_unit_for_day(self, date, duty, selected_units, faculty_plan):
        """Выбрать подразделение для наряда на конкретный день"""
        # Простая ротация по порядку
        day_index = date.day - 1
        unit_index = day_index % len(selected_units)
        selected_unit = selected_units[unit_index]
        
        return selected_unit
    
    def _create_duty_schedule(self, duty, date, assigned_unit, faculty_plan):
        """Создать запись DutySchedule"""
        
        try:
            duty_schedule = DutySchedule(
                duty=duty,
                date=date,
                is_manually_assigned=False
            )
            
            # Назначаем подразделение
            if assigned_unit == 'management':
                duty_schedule.assigned_faculty = self.faculty
                duty_schedule.assigned_department = None
            elif assigned_unit.startswith('department_'):
                dept_id = assigned_unit.replace('department_', '')
                department = Department.objects.get(id=dept_id, faculty=self.faculty)
                duty_schedule.assigned_department = department
                duty_schedule.assigned_faculty = None
            else:
                print(f"  ❌ Неизвестный тип подразделения: {assigned_unit}")
                return False
            
            duty_schedule.save()
            return True
        except Exception as e:
            print(f"❌ Ошибка при создании DutySchedule: {e}")
            return False
# ==================== VIEWS ====================

class FacultyDashboardView(HasFacultyMixin, TemplateView):
    template_name = 'profiles/faculty/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not hasattr(user, 'faculty') or not user.faculty:
            return context

        departments = Department.objects.filter(faculty=user.faculty)
        departments_stats = {
            'total': departments.count(),
            'total_staff': People.objects.filter(department__in=departments).count(),
            'avg_workload': People.objects.filter(department__in=departments).aggregate(Avg('workload'))['workload__avg'] or 0,
        }

        top_departments = departments.annotate(
            staff_count=Count('people'),
            avg_workload=Avg('people__workload')
        ).order_by('-staff_count')[:5]

        context.update({
            'user': user,
            'faculty': user.faculty,
            'departments_count': departments_stats['total'],
            'staff_count': departments_stats['total_staff'],
            'avg_workload': round(departments_stats['avg_workload'], 1),
            'top_departments': top_departments,
        })

        return context


class FacultyStaffView(HasFacultyMixin, TemplateView):
    template_name = 'profiles/faculty/staff/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not hasattr(user, 'faculty') or not user.faculty:
            return context

        department_id = self.request.GET.get('department')
        duty_id = self.request.GET.get('duty')

        staff = People.objects.filter(
            Q(department__faculty=user.faculty) | 
            Q(faculty=user.faculty, department__isnull=True)
        ).annotate(
            is_management=Case(
                When(department__isnull=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).select_related('department', 'rank').order_by('full_name')

        filtered_duties = Duty.objects.filter(
            Q(is_commandant=True) |
            Q(faculty=user.faculty, department__isnull=True)
        ).distinct()

        departments = Department.objects.filter(faculty=user.faculty)

        if department_id == 'management':
            staff = staff.filter(department__isnull=True)
        elif department_id:
            staff = staff.filter(department_id=department_id)

        if duty_id:
            staff = staff.filter(
                Q(department_duty_permissions__duty_id=duty_id) |
                Q(faculty_duty_permissions__duty_id=duty_id)
            ).distinct()

        today = timezone.now().date()
        table_items = []

        for idx, person in enumerate(staff, start=1):
            missing = None

            if person.department:
                missing = DepartmentMissing.objects.filter(
                    person=person,
                ).first()
            else:
                missing = FacultyMissing.objects.filter(
                    person=person,
                ).first()

            missing_info = '-'
            if missing:
                missing_info = f"{missing.start_date.strftime('%d.%m.%Y')} – {missing.end_date.strftime('%d.%m.%Y')}"

            dept_name = str(person.department) if person.department else 'Управление'

            table_items.append({
                'url': reverse('faculty:staff_detail', args=[person.pk]),
                'fields': [
                    {'value': idx},
                    {'value': person.full_name},
                    {'value': str(person.rank) if person.rank else '-'},
                    {'value': dept_name},
                    {'value': missing_info}
                ]
            })

        headers = [
            {'label': '#'},
            {'label': 'ФИО'},
            {'label': 'Звание'},
            {'label': 'Подразделение'},
            {'label': 'Освобождение'}
        ]

        context.update({
            'faculty': user.faculty,
            'headers': headers,
            'table_items': table_items,
            'departments': departments,
            'duties': filtered_duties,
            'selected_department': department_id,
            'selected_duty': duty_id,
            'total_people': len(table_items),
        })

        return context


class StaffDetailView(HasFacultyMixin, TemplateView):
    template_name = 'profiles/faculty/staff/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person_id = self.kwargs['pk']
        try:
            person = People.objects.get(pk=person_id)
        except People.DoesNotExist:
            person = None

        context['person'] = person
        return context


# faculty/views.py

class FacultyAcademicDutiesView(HasFacultyMixin, TemplateView):
    """Просмотр распределенных на факультет нарядов коменданта"""
    template_name = 'profiles/faculty/academic_duties.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        faculty = user.faculty
        
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        
        try:
            if year and month:
                current_date = datetime(int(year), int(month), 1).date()
            else:
                current_date = timezone.now().date().replace(day=1)
        except:
            current_date = timezone.now().date().replace(day=1)
        
        # ИСПРАВЛЕНИЕ: Фильтруем наряды с is_commandant=True
        schedules = DutySchedule.objects.filter(
            Q(assigned_faculty=faculty) | 
            Q(assigned_department__faculty=faculty)
        ).filter(
            date__year=current_date.year,
            date__month=current_date.month,
            duty__is_commandant=True  # Фильтр по существующему полю
        ).select_related('duty', 'assigned_faculty', 'assigned_department').order_by('date')
        
        schedules_by_date = defaultdict(list)
        for schedule in schedules:
            schedules_by_date[schedule.date].append(schedule)
        
        sorted_dates = sorted(schedules_by_date.keys())
        total_duties = schedules.count()
        
        # Считаем количество людей
        total_people = sum(s.duty.people_count for s in schedules)
        
        # Статистика по подразделениям
        dept_distribution = {}
        for schedule in schedules:
            if schedule.assigned_department:
                dept_name = schedule.assigned_department.name
                dept_distribution[dept_name] = dept_distribution.get(dept_name, 0) + 1
            else:
                dept_distribution['Управление факультета'] = dept_distribution.get('Управление факультета', 0) + 1
        
        prev_month = self._get_adjacent_month(current_date, -1)
        next_month = self._get_adjacent_month(current_date, 1)
        
        context.update({
            'faculty': faculty,
            'current_date': current_date,
            'prev_month': prev_month,
            'next_month': next_month,
            'schedules': schedules,
            'schedules_by_date': dict(schedules_by_date),
            'sorted_dates': sorted_dates,
            'total_duties': total_duties,
            'total_people': total_people,
            'dept_distribution': dept_distribution,
            'today': timezone.now().date(),
        })
        
        return context
    
    def _get_adjacent_month(self, date, delta):
        """Получить соседний месяц"""
        year = date.year
        month = date.month + delta
        
        if month > 12:
            year += 1
            month = 1
        elif month < 1:
            year -= 1
            month = 12
            
        return datetime(year, month, 1).date()

class FacultyDutyPlanView(HasFacultyMixin, TemplateView):
    """Планировщик факультетских нарядов"""
    template_name = 'profiles/faculty/duty_plan.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = self.request.user.faculty
        
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        
        try:
            if year and month:
                current_date = datetime(int(year), int(month), 1).date()
            else:
                current_date = timezone.now().date().replace(day=1)
        except:
            current_date = timezone.now().date().replace(day=1)
        
        # Получаем или создаем план
        faculty_plan, created = FacultyMonthlyPlan.objects.get_or_create(
            faculty=faculty,
            month=current_date,
            defaults={
                'duty_schedule_settings': {},
                'selected_units': ['management']
            }
        )
        
        duties = Duty.objects.filter(
            faculty=faculty,
            department__isnull=True,
            is_commandant=False
        )
        
        schedules = DutySchedule.objects.filter(
            duty__in=duties,
            date__year=current_date.year,
            date__month=current_date.month
        ).select_related('duty', 'assigned_faculty', 'assigned_department')
        
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(current_date.year, current_date.month)
        
        calendar_weeks = []
        for week in month_days:
            calendar_week = []
            for day in week:
                if day == 0:
                    calendar_week.append({'day': None, 'date': None, 'schedules': []})
                else:
                    day_date = datetime(current_date.year, current_date.month, day).date()
                    day_schedules = [s for s in schedules if s.date == day_date]
                    calendar_week.append({
                        'day': day,
                        'date': day_date,
                        'schedules': day_schedules,
                        'is_today': day_date == timezone.now().date()
                    })
            calendar_weeks.append(calendar_week)
        
        # Используем get_duty_schedule_display для отображения в шаблоне
        duty_schedules_display = {}
        if faculty_plan:
            for duty in duties:
                schedule_data = faculty_plan.get_duty_schedule_display(duty)
                duty_schedules_display[duty.id] = schedule_data
        
        departments = faculty.departments.all()
        
        selected_units_list = faculty_plan.selected_units if faculty_plan else ['management']
        
        # Вызываем метод для получения статистики
        unit_stats = self._get_unit_stats(schedules, faculty)
        
        # Список дней недели для шаблона
        weekday_choices = [
            ('0', 'Понедельник'),
            ('1', 'Вторник'),
            ('2', 'Среда'),
            ('3', 'Четверг'),
            ('4', 'Пятница'),
            ('5', 'Суббота'),
            ('6', 'Воскресенье')
        ]
        
        # Передаем URL в контекст
        context.update({
            'faculty': faculty,
            'current_date': current_date,
            'prev_month': self._get_adjacent_month(current_date, -1),
            'next_month': self._get_adjacent_month(current_date, 1),
            'duties': duties,
            'faculty_plan': faculty_plan,
            'calendar_weeks': calendar_weeks,
            'schedules': schedules,
            'duty_schedules': duty_schedules_display,  # Передаем данные для отображения
            'departments': departments,
            'selected_units_list': selected_units_list,
            'unit_stats': unit_stats,
            'weekday_choices': weekday_choices,
        })
        
        return context
    
    def _get_unit_stats(self, schedules, faculty):
        """Статистика по подразделениям факультета"""
        stats = defaultdict(lambda: {'count': 0, 'duties': set(), 'name': ''})
        
        # Добавляем управление факультета
        stats['management'] = {
            'name': 'Управление факультета',
            'count': 0,
            'duties': set()
        }
        
        # Добавляем кафедры факультета
        for department in faculty.departments.all():
            stats[f'department_{department.id}'] = {
                'name': department.name,
                'count': 0,
                'duties': set()
            }
        
        # Подсчитываем статистику
        for schedule in schedules:
            if schedule.assigned_faculty == faculty:
                stats['management']['count'] += 1
                stats['management']['duties'].add(schedule.duty.duty_name)
            elif schedule.assigned_department and schedule.assigned_department.faculty == faculty:
                key = f"department_{schedule.assigned_department.id}"
                if key in stats:
                    stats[key]['count'] += 1
                    stats[key]['duties'].add(schedule.duty.duty_name)
        
        return dict(stats)
    
    def _get_adjacent_month(self, date, delta):
        """Получить соседний месяц"""
        year = date.year
        month = date.month + delta
        
        if month > 12:
            year += 1
            month = 1
        elif month < 1:
            year -= 1
            month = 12
            
        return datetime(year, month, 1).date()
    

    def post(self, request, *args, **kwargs):
        """Сохранение настроек расписания"""
        duty_id = request.POST.get('duty_id')
        
        year = request.GET.get('year', timezone.now().year)
        month = request.GET.get('month', timezone.now().month)
        current_date = datetime(int(year), int(month), 1).date()
        
        faculty = request.user.faculty
        
        faculty_plan, created = FacultyMonthlyPlan.objects.get_or_create(
            faculty=faculty,
            month=current_date,
            defaults={'duty_schedule_settings': {}}
        )
        
        if duty_id:
            duty = get_object_or_404(Duty, id=duty_id, faculty=faculty)
            
            # Получаем данные из формы
            schedule_data = {
                'ranges': request.POST.getlist('ranges[]'),
                'specific_dates': request.POST.getlist('specific_dates[]'),
                'weekdays': request.POST.getlist('weekdays[]'),
            }
            
            # Отладочная информация
            print(f"📥 Получены данные для duty_id={duty_id}:")
            print(f"  - ranges: {schedule_data['ranges']}")
            print(f"  - specific_dates: {schedule_data['specific_dates']}")
            print(f"  - weekdays: {schedule_data['weekdays']}")
            
            # Фильтруем пустые значения
            schedule_data['ranges'] = [r.strip() for r in schedule_data['ranges'] if r and r.strip()]
            schedule_data['specific_dates'] = [d.strip() for d in schedule_data['specific_dates'] if d and d.strip()]
            
            # Нормализуем дни недели - ИСПРАВЛЕННЫЙ КОД
            normalized_weekdays = []
            for day_setting in schedule_data['weekdays']:
                if day_setting and day_setting.strip():
                    # Вместо вызова normalize_weekday_setting делаем прямое преобразование
                    day_str = day_setting.strip().lower()
                    
                    # Маппинг русских названий дней недели в числа
                    weekday_map = {
                        'понедельник': 0,
                        'вторник': 1, 
                        'среда': 2,
                        'четверг': 3,
                        'пятница': 4,
                        'суббота': 5,
                        'воскресенье': 6,
                        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6  # Если уже пришло число
                    }
                    
                    # Если это название дня недели или число, преобразуем в число
                    if day_str in weekday_map:
                        normalized_weekdays.append(weekday_map[day_str])
                    elif day_str.isdigit() and 0 <= int(day_str) <= 6:
                        normalized_weekdays.append(int(day_str))
                    else:
                        print(f"⚠️ Пропущен некорректный день недели: {day_setting}")
            
            # Сохраняем как строковые представления чисел для JSON
            schedule_data['weekdays'] = [str(day) for day in normalized_weekdays]
            
            print(f"✅ Нормализованные дни недели (строки): {schedule_data['weekdays']}")
            
            # Сохраняем настройки
            current_settings = faculty_plan.duty_schedule_settings.copy()
            
            if not any(schedule_data.values()):
                # Если все пусто - удаляем настройки для этого наряда
                if str(duty.id) in current_settings:
                    del current_settings[str(duty.id)]
            else:
                # Сохраняем новые настройки
                current_settings[str(duty.id)] = schedule_data
            
            faculty_plan.duty_schedule_settings = current_settings
            faculty_plan.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Настройки сохранены',
                    'settings': schedule_data
                })
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Некорректный запрос'
            })
        
        redirect_url = reverse('faculty:duty_plan') + f'?year={year}&month={month}'
        return redirect(redirect_url)


class GenerateFacultyPlanView(HasFacultyMixin, View):
    """Генерация плана факультетских нарядов"""
    def post(self, request, *args, **kwargs):
        try:
            year = request.POST.get('year')
            month = request.POST.get('month')
            duty_ids = request.POST.get('duties', '').split(',')
            selected_units = request.POST.getlist('selected_units', [])
            
            duty_ids = [duty_id for duty_id in duty_ids if duty_id]
            selected_units = [unit for unit in selected_units if unit]
            
            if not duty_ids:
                return JsonResponse({'success': False, 'error': 'Выберите наряды'})
            
            if not selected_units:
                return JsonResponse({'success': False, 'error': 'Выберите подразделения'})
            
            year = int(year)
            month = int(month)
            current_date = datetime(year, month, 1).date()
            faculty = request.user.faculty
            
            faculty_plan, created = FacultyMonthlyPlan.objects.get_or_create(
                faculty=faculty,
                month=current_date,
                defaults={'duty_schedule_settings': {}}
            )
            
            faculty_plan.selected_units = selected_units
            
            # Сохраняем выбранные наряды в настройках (если их нет)
            current_settings = faculty_plan.duty_schedule_settings.copy()
            for duty_id in duty_ids:
                if duty_id not in current_settings:
                    current_settings[duty_id] = {'ranges': [], 'specific_dates': [], 'weekdays': []}
            
            faculty_plan.duty_schedule_settings = current_settings
            faculty_plan.save()
            
            distribution_service = FacultyDistributionService(faculty, current_date)
            schedule_count = distribution_service.generate_schedule(faculty_plan)
            
            return JsonResponse({
                'success': True,
                'count': schedule_count,
                'units_count': len(selected_units),
                'message': f'План факультетских нарядов сгенерирован! Создано {schedule_count} записей.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ResetFacultyPlanView(HasFacultyMixin, View):
    """Сброс плана факультета"""
    def post(self, request, *args, **kwargs):
        year = request.POST.get('year')
        month = request.POST.get('month')
        
        try:
            year = int(year)
            month = int(month)
            current_date = datetime(year, month, 1).date()
            faculty = request.user.faculty
            
            faculty_plan = FacultyMonthlyPlan.objects.filter(
                faculty=faculty,
                month=current_date
            ).first()
            
            if faculty_plan:
                schedule_count = DutySchedule.objects.filter(
                    duty__faculty=faculty,
                    duty__department__isnull=True,
                    date__year=year,
                    date__month=month
                ).count()
                
                DutySchedule.objects.filter(
                    duty__faculty=faculty,
                    duty__department__isnull=True,
                    date__year=year,
                    date__month=month
                ).delete()
                
                faculty_plan.duty_schedule_settings = {}
                faculty_plan.selected_units = []
                faculty_plan.is_generated = False
                faculty_plan.last_generated_at = None
                faculty_plan.save()
                
                messages.success(
                    request,
                    f'План факультетских нарядов сброшен. Удалено {schedule_count} записей.'
                )
            
        except Exception as e:
            messages.error(request, f'Ошибка при сбросе: {str(e)}')
        
        redirect_url = reverse('faculty:duty_plan') + f'?year={year}&month={month}'
        return redirect(redirect_url)


class UpdateFacultyScheduleView(HasFacultyMixin, View):
    """Обновление назначения факультетского наряда"""
    def post(self, request, *args, **kwargs):
        try:
            schedule_id = kwargs.get('pk')
            unit_type = request.POST.get('unit_type')
            unit_id = request.POST.get('unit_id')
            
            schedule = get_object_or_404(DutySchedule, id=schedule_id)
            faculty = request.user.faculty
            
            if schedule.duty.faculty != faculty:
                return JsonResponse({'success': False, 'error': 'Нет доступа'})
            
            schedule.assigned_faculty = None
            schedule.assigned_department = None
            
            unit_name = ""
            if unit_type == 'management':
                schedule.assigned_faculty = faculty
                unit_name = "Управление факультета"
            elif unit_type == 'department':
                department = get_object_or_404(Department, id=unit_id, faculty=faculty)
                schedule.assigned_department = department
                unit_name = f"Кафедра: {department.name}"
            else:
                return JsonResponse({'success': False, 'error': 'Неверный тип'})
            
            schedule.is_manually_assigned = True
            schedule.save()
            
            # Определяем тип наряда
            duty_type = 'rotating'
            if schedule.duty.assigned_faculty or schedule.duty.assigned_department:
                duty_type = 'fixed'
            
            return JsonResponse({
                'success': True,
                'unit_name': unit_name,
                'unit_type': unit_type,
                'duty_type': duty_type,
                'schedule_id': schedule_id,
                'is_manually_assigned': True
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class FacultyPlanDetailView(HasFacultyMixin, DetailView):
    """Детальный просмотр плана факультета"""
    model = FacultyMonthlyPlan
    template_name = 'profiles/faculty/plan_detail.html'
    context_object_name = 'plan'

    def get_queryset(self):
        return FacultyMonthlyPlan.objects.filter(faculty=self.request.user.faculty)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.object
        
        schedules = DutySchedule.objects.filter(
            duty__faculty=plan.faculty,
            duty__department__isnull=True,
            date__year=plan.month.year,
            date__month=plan.month.month
        ).select_related('duty', 'assigned_faculty', 'assigned_department')
        
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(plan.month.year, plan.month.month)
        
        calendar_weeks = []
        for week in month_days:
            calendar_week = []
            for day in week:
                if day == 0:
                    calendar_week.append({'day': None})
                else:
                    day_date = datetime(plan.month.year, plan.month.month, day).date()
                    day_schedules = [s for s in schedules if s.date == day_date]
                    calendar_week.append({
                        'day': day,
                        'date': day_date,
                        'schedules': day_schedules,
                        'is_today': day_date == timezone.now().date()
                    })
            calendar_weeks.append(calendar_week)
        
        context.update({
            'schedules': schedules,
            'calendar_weeks': calendar_weeks,
            'total_schedules': schedules.count(),
            'departments': plan.faculty.departments.all(),
        })
        
        return context
    

class FacultyPlanListView(HasFacultyMixin, ListView):
    """Список всех созданных планов факультета"""
    model = FacultyMonthlyPlan
    template_name = 'profiles/faculty/plan_list.html'
    context_object_name = 'plans'
    ordering = ['-month']
    paginate_by = 10

    def get_queryset(self):
        return FacultyMonthlyPlan.objects.filter(
            faculty=self.request.user.faculty
        ).select_related('faculty')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = self.request.user.faculty
        
        # Добавляем количество расписаний для каждого плана
        for plan in context['plans']:
            plan.schedule_count = DutySchedule.objects.filter(
                duty__faculty=faculty,
                duty__department__isnull=True,
                date__year=plan.month.year,
                date__month=plan.month.month
            ).count()
        
        # Статистика
        active_plans_count = FacultyMonthlyPlan.objects.filter(
            faculty=faculty,
            is_generated=True
        ).count()
        
        total_schedules = DutySchedule.objects.filter(
            duty__faculty=faculty,
            duty__department__isnull=True
        ).count()
        
        departments = faculty.departments.all()
        
        context.update({
            'faculty': faculty,
            'active_plans_count': active_plans_count,
            'total_schedules': total_schedules,
            'departments': departments,
        })
        
        return context

# faculty/views.py - ДОБАВЛЯЕМ В КОНЕЦ ФАЙЛА

class DeleteFacultyPlanView(HasFacultyMixin, View):
    """Удаление плана факультета"""
    def post(self, request, *args, **kwargs):
        plan_id = kwargs.get('pk')
        faculty = request.user.faculty
        
        try:
            plan = get_object_or_404(FacultyMonthlyPlan, id=plan_id, faculty=faculty)
            
            # Удаляем все связанные расписания
            schedule_count = DutySchedule.objects.filter(
                duty__faculty=faculty,
                duty__department__isnull=True,
                date__year=plan.month.year,
                date__month=plan.month.month
            ).delete()[0]
            
            # Сохраняем информацию для сообщения
            plan_month = plan.month.strftime('%B %Y')
            
            # Удаляем сам план
            plan.delete()
            
            messages.success(
                request,
                f'План на {plan_month} успешно удален. Удалено {schedule_count} записей расписаний.'
            )
            
        except Exception as e:
            messages.error(request, f'Ошибка при удалении плана: {str(e)}')
        
        return redirect('faculty:plan_list')