from django.views.generic import TemplateView, FormView, View, ListView, DetailView
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
import calendar
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

from core.mixins import IsCommandantMixin
from people.models import People
from unit.models import Faculty, Department
from duty.models import Duty, DutySchedule, MonthlyDutyPlan
from duty.forms import MonthlyPlanForm, DutyScheduleSettingsForm
from duty.services import DutyDistributionService
from missing.models import DepartmentMissing
from permission.models import DepartmentDutyPermission
from duty.utils import normalize_weekday_setting


class CommandantDashboardView(IsCommandantMixin, TemplateView):
    template_name = 'profiles/commandant/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update({
            'user': user,
        })
        return context


class CommandantStaffListView(IsCommandantMixin, TemplateView):
    template_name = 'profiles/commandant/staff/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем параметры фильтрации
        unit_id = self.request.GET.get('unit')
        duty_id = self.request.GET.get('duty')

        # Формируем список доступных подразделений
        faculties = Faculty.objects.annotate(
            staff_count=Count('departments__people')
        ).order_by('name')

        departments_without_faculty = Department.objects.filter(faculty__isnull=True).annotate(
            staff_count=Count('people')
        ).order_by('name')

        units = []

        # Добавляем факультеты
        for f in faculties:
            unit_entry = {
                'type': 'faculty',
                'id': f'id_f_{f.id}',
                'name': f'{f.name} факультет',
                'staff_count': f.staff_count,
                'is_selected': f'id_f_{f.id}' == unit_id,
            }
            units.append(unit_entry)

        # Добавляем кафедры без факультета
        for d in departments_without_faculty:
            unit_entry = {
                'type': 'department',
                'id': f'id_d_{d.id}',
                'name': f'{d.name} кафедра',
                'staff_count': d.staff_count,
                'is_selected': f'id_d_{d.id}' == unit_id,
            }
            units.append(unit_entry)

        # Базовая выборка
        staff = People.objects.select_related('department', 'rank')

        # Определяем, что выбрано: факультет или кафедра без факультета
        if unit_id:
            if unit_id.startswith('id_f_'):
                faculty_id = int(unit_id.replace('id_f_', ''))
                staff = staff.filter(department__faculty_id=faculty_id) | staff.filter(
                    faculty_id=faculty_id, department__isnull=True
                )

            elif unit_id.startswith('id_d_'):
                department_id = int(unit_id.replace('id_d_', ''))
                staff = staff.filter(department_id=department_id)

        # Фильтр по допуску к наряду
        if duty_id:
            staff = staff.filter(department_duty_permissions__duty_id=duty_id).distinct()

        # Формируем данные для таблицы
        today = timezone.now().date()
        table_items = []

        for idx, person in enumerate(staff, start=1):
            missing = DepartmentMissing.objects.filter(
                person=person,
                start_date__lte=today,
                end_date__gte=today
            ).first()

            missing_info = '-'
            if missing:
                missing_info = f"{missing.get_reason_display()} ({missing.start_date.strftime('%d.%m')} – {missing.end_date.strftime('%d.%m')})"

            dept_name = str(person.department) if person.department else (
                f'Управление факультета {person.faculty}' if person.faculty else '-'
            )

            table_items.append({
                'url': reverse('commandant:staff_detail', args=[person.pk]),
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
            {'label': 'Кафедра'},
            {'label': 'Освобождение'}
        ]

        context.update({
            'headers': headers,
            'table_items': table_items,
            'units': units,
            'duties': Duty.objects.filter(is_commandant=True),
            'selected_unit': unit_id,
            'selected_duty': duty_id,
            'total_people': len(table_items),
        })

        return context


class CommandantStaffDetailView(IsCommandantMixin, TemplateView):
    template_name = 'profiles/commandant/staff/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person_id = self.kwargs['pk']
        try:
            person = People.objects.select_related('department', 'rank').get(pk=person_id)
        except People.DoesNotExist:
            person = None

        context['person'] = person
        return context


class DutyPlanView(IsCommandantMixin, TemplateView):
    template_name = 'profiles/commandant/duty_plan.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем месяц из параметров
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        
        try:
            year = int(year) if year else timezone.now().year
            month = int(month) if month else timezone.now().month
            current_date = datetime(year, month, 1).date()
        except (ValueError, TypeError):
            current_date = timezone.now().date().replace(day=1)
        
        # Проверяем существующий план
        monthly_plan = MonthlyDutyPlan.objects.filter(month=current_date).first()
        
        # Получаем все наряды коменданта
        duties = Duty.objects.filter(is_commandant=True)
        
        # Получаем расписание для отображения
        schedules = DutySchedule.objects.filter(
            date__year=year,
            date__month=month
        ).select_related('duty', 'assigned_faculty', 'assigned_department')
        
        # Создаем календарь с реальными данными
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)
        
        # Форматируем дни для шаблона с реальными нарядами
        calendar_weeks = []
        for week in month_days:
            calendar_week = []
            for day in week:
                if day == 0:
                    calendar_week.append({'day': None, 'date': None, 'schedules': []})
                else:
                    day_date = datetime(year, month, day).date()
                    day_schedules = [s for s in schedules if s.date == day_date]
                    calendar_week.append({
                        'day': day,
                        'date': day_date,
                        'schedules': day_schedules,
                        'is_today': day_date == timezone.now().date()
                    })
            calendar_weeks.append(calendar_week)
        
        # Получаем настройки расписания для каждого наряда с корректной структурой
        duty_schedules = {}
        if monthly_plan:
            for duty in duties:
                schedule_data = monthly_plan.get_duty_schedule(duty)
                # УБРАН ФИЛЬТР, КОТОРЫЙ ИСКЛЮЧАЛ ДНИ НЕДЕЛИ
                filtered_schedule = {
                    'ranges': [r for r in schedule_data.get('ranges', []) if r and r.strip()],
                    'specific_dates': [d for d in schedule_data.get('specific_dates', []) if d and d.strip()],
                    'weekdays': [w for w in schedule_data.get('weekdays', []) if w and w.strip()],  # УБРАН ФИЛЬТР
                }
                duty_schedules[duty.id] = filtered_schedule
        
        # Статистика по подразделениям
        unit_stats = self.get_unit_stats(schedules)
        
        # Получаем факультеты и кафедры для выбора с аннотацией количества сотрудников
        faculties = Faculty.objects.annotate(
            staff_count=Count('departments__people', distinct=True) + Count('people', distinct=True)
        ).order_by('name')
        
        independent_departments = Department.objects.filter(faculty__isnull=True).annotate(
            staff_count=Count('people', distinct=True)
        ).order_by('name')
        
        # Получаем список выбранных подразделений для шаблона
        selected_units_list = []
        if monthly_plan and monthly_plan.selected_units:
            selected_units_list = monthly_plan.selected_units
        
        context.update({
            'current_date': current_date,
            'prev_month': self.get_adjacent_month(current_date, -1),
            'next_month': self.get_adjacent_month(current_date, 1),
            'duties': duties,
            'monthly_plan': monthly_plan,
            'calendar_weeks': calendar_weeks,
            'schedules': schedules,
            'duty_schedules': duty_schedules,
            'unit_stats': unit_stats,
            'schedule_form': DutyScheduleSettingsForm(),
            'faculties': faculties,
            'independent_departments': independent_departments,
            'selected_units_list': selected_units_list,  # Добавлено для шаблона
        })
        
        return context
    
    def get_unit_stats(self, schedules):
        """Статистика по подразделениям"""
        stats = defaultdict(lambda: {'count': 0, 'duties': set(), 'name': ''})
        
        for schedule in schedules:
            if schedule.assigned_faculty:
                key = f"faculty_{schedule.assigned_faculty.id}"
                stats[key]['name'] = schedule.assigned_faculty.name
                stats[key]['count'] += 1
                stats[key]['duties'].add(schedule.duty.duty_name)
            elif schedule.assigned_department:
                key = f"department_{schedule.assigned_department.id}"
                stats[key]['name'] = schedule.assigned_department.name
                stats[key]['count'] += 1
                stats[key]['duties'].add(schedule.duty.duty_name)

        return dict(stats)
    
    def post(self, request, *args, **kwargs):
        """Обработка сохранения комбинированных настроек расписания"""
        duty_id = request.POST.get('duty_id')
        
        # Получаем месяц из GET параметров
        year = request.GET.get('year', timezone.now().year)
        month = request.GET.get('month', timezone.now().month)
        current_date = datetime(int(year), int(month), 1).date()
        
        # Создаем или получаем месячный план
        monthly_plan, created = MonthlyDutyPlan.objects.get_or_create(
            month=current_date
        )
        
        # Получаем наряд
        duty = get_object_or_404(Duty, id=duty_id)
        
        # Формируем комбинированные данные расписания
        schedule_data = {
            'ranges': request.POST.getlist('ranges[]'),
            'specific_dates': request.POST.getlist('specific_dates[]'),
            'weekdays': request.POST.getlist('weekdays[]'),
        }
        
        print(f"💾 Получены данные для наряда {duty_id}:")
        print(f"   - Диапазоны: {schedule_data['ranges']}")
        print(f"   - Конкретные даты: {schedule_data['specific_dates']}")
        print(f"   - Дни недели: {schedule_data['weekdays']} (типы: {[type(w).__name__ for w in schedule_data['weekdays']]})")
        
        # Фильтруем пустые значения и нормализуем дни недели
        schedule_data['ranges'] = [r.strip() for r in schedule_data['ranges'] if r and r.strip()]
        schedule_data['specific_dates'] = [d.strip() for d in schedule_data['specific_dates'] if d and d.strip()]
        
        # ВАЖНО: Нормализуем дни недели к числам
        normalized_weekdays = []
        for day_setting in schedule_data['weekdays']:
            if day_setting and day_setting.strip():
                normalized = normalize_weekday_setting(day_setting.strip())
                if normalized is not None:
                    normalized_weekdays.append(str(normalized))  # Сохраняем как строку для JSON
                else:
                    print(f"⚠️ Не удалось нормализовать день недели: '{day_setting}'")
        
        schedule_data['weekdays'] = normalized_weekdays
        
        print(f"💾 Очищенные и нормализованные данные для наряда {duty_id}:")
        print(f"   - Диапазоны: {schedule_data['ranges']}")
        print(f"   - Конкретные даты: {schedule_data['specific_dates']}")
        print(f"   - Дни недели (нормализованные): {schedule_data['weekdays']}")
        
        # Получаем текущие настройки
        current_settings = monthly_plan.duty_schedule_settings.copy()
        
        # Если все поля пустые - полностью удаляем настройки для этого наряда
        if not any(schedule_data.values()):
            if str(duty.id) in current_settings:
                del current_settings[str(duty.id)]
                monthly_plan.duty_schedule_settings = current_settings
                monthly_plan.save()
                messages.success(request, f'Настройки расписания для "{duty.duty_name}" полностью очищены')
                print(f"🗑️ Удалены настройки для наряда {duty_id}")
        else:
            # Сохраняем настройки (включая дни недели)
            current_settings[str(duty.id)] = schedule_data
            monthly_plan.duty_schedule_settings = current_settings
            monthly_plan.save()
            messages.success(request, f'Настройки расписания для "{duty.duty_name}" сохранены')
            print(f"💾 Сохранены настройки для наряда {duty_id}: {schedule_data}")
        
        # ВАЖНО: Возвращаем JSON ответ для AJAX запросов
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'duty_id': duty_id,
                'settings': schedule_data
            })
        
        # Редирект на ту же страницу с сохранением месяца
        redirect_url = reverse('commandant:duty_plan') + f'?year={year}&month={month}'
        return redirect(redirect_url)
    
    def get_adjacent_month(self, date, delta):
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


# В GenerateDutyPlanView добавьте валидацию:
class GenerateDutyPlanView(IsCommandantMixin, View):
    def post(self, request, *args, **kwargs):
        print("🚀 НАЧАЛО ГЕНЕРАЦИИ ПЛАНА")
        
        year = request.POST.get('year')
        month = request.POST.get('month')
        duty_ids = request.POST.get('duties', '').split(',')
        selected_units = request.POST.getlist('selected_units', [])
        
        print(f"📥 Полученные данные:")
        print(f"   - year: {year}")
        print(f"   - month: {month}") 
        print(f"   - duty_ids: {duty_ids}")
        print(f"   - selected_units: {selected_units}")
        
        # Убираем пустые значения
        duty_ids = [duty_id for duty_id in duty_ids if duty_id]
        selected_units = [unit for unit in selected_units if unit]
        
        print(f"📋 Очищенные данные:")
        print(f"   - duty_ids: {duty_ids}")
        print(f"   - selected_units: {selected_units}")
        
        # Валидация
        if not duty_ids:
            print("❌ Ошибка: не выбраны наряды")
            return JsonResponse({'success': False, 'error': 'Выберите хотя бы один наряд'})
        
        if not selected_units:
            print("❌ Ошибка: не выбраны подразделения")
            return JsonResponse({'success': False, 'error': 'Выберите хотя бы одно подразделение'})
        
        try:
            year = int(year)
            month = int(month)
            current_date = datetime(year, month, 1).date()
            
            print(f"📅 Дата плана: {current_date}")
            
            # Создаем или обновляем месячный план
            monthly_plan, created = MonthlyDutyPlan.objects.get_or_create(
                month=current_date
            )
            
            print(f"📊 План: ID={monthly_plan.id}, создан={created}")
            
            # Добавляем выбранные наряды
            duties = Duty.objects.filter(id__in=duty_ids)
            monthly_plan.set_duties(duties)
            
            print(f"✅ Добавлены наряды: {[d.duty_name for d in duties]}")
            
            # Сохраняем выбранные подразделения
            monthly_plan.selected_units = selected_units
            monthly_plan.save()
            
            print(f"✅ Сохранены подразделения: {selected_units}")
            
            # Генерируем расписание
            distribution_service = DutyDistributionService(current_date)
            schedule_count = distribution_service.generate_schedule(monthly_plan)
            
            print(f"✅ Сгенерировано расписаний: {schedule_count}")
            
            # ОБНОВЛЯЕМ план после генерации
            monthly_plan.refresh_from_db()
            print(f"🔄 План после генерации: is_generated={monthly_plan.is_generated}")
            
            messages.success(
                request, 
                f'График нарядов успешно сгенерирован! Создано {schedule_count} записей.'
            )
            
            return JsonResponse({
                'success': True, 
                'count': schedule_count,
                'units_count': len(selected_units)
            })
            
        except Exception as e:
            print(f"❌ Ошибка при генерации: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
        
class ResetDutyPlanView(IsCommandantMixin, View):
    def post(self, request, *args, **kwargs):
        year = request.POST.get('year')
        month = request.POST.get('month')
        
        try:
            year = int(year)
            month = int(month)
            current_date = datetime(year, month, 1).date()
            
            # Находим план
            monthly_plan = MonthlyDutyPlan.objects.filter(month=current_date).first()
            
            if monthly_plan:
                # Удаляем все расписания для этого месяца
                schedule_count = DutySchedule.objects.filter(
                    date__year=year,
                    date__month=month
                ).count()
                
                DutySchedule.objects.filter(
                    date__year=year,
                    date__month=month
                ).delete()
                
                # ✅ ПОЛНЫЙ СБРОС ВСЕХ НАСТРОЕК
                monthly_plan.duty_schedule_settings = {}  # Очищаем параметры расписания
                monthly_plan.selected_units = []  # Очищаем выбранные подразделения
                monthly_plan.duties.clear()  # Очищаем выбранные наряды
                monthly_plan.is_generated = False
                monthly_plan.last_generated_at = None
                monthly_plan.save()
                
                messages.success(
                    request, 
                    f'График нарядов за {current_date.strftime("%B %Y")} полностью сброшен. '
                    f'Удалено {schedule_count} записей. Все настройки и параметры очищены.'
                )
            else:
                messages.info(request, f'План на {current_date.strftime("%B %Y")} не найден')
            
        except Exception as e:
            messages.error(request, f'Ошибка при сбросе графика: {str(e)}')
        
        # Редирект обратно на страницу плана
        redirect_url = reverse('commandant:duty_plan') + f'?year={year}&month={month}'
        return redirect(redirect_url)
    

class PlanListView(IsCommandantMixin, ListView):
    """Список всех созданных планов"""
    model = MonthlyDutyPlan
    template_name = 'profiles/commandant/plans/list.html'
    context_object_name = 'plans'
    ordering = ['-month']
    paginate_by = 10

    def get_queryset(self):
        # ФИЛЬТРУЕМ ТОЛЬКО СГЕНЕРИРОВАННЫЕ ПЛАНЫ
        return MonthlyDutyPlan.objects.filter(
            is_generated=True
        ).select_related().prefetch_related('duties').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем количество расписаний для каждого плана
        for plan in context['plans']:
            plan.schedule_count = DutySchedule.objects.filter(
                date__year=plan.month.year,
                date__month=plan.month.month
            ).count()
        
        return context


class PlanDetailView(IsCommandantMixin, DetailView):
    """Детальный просмотр плана"""
    model = MonthlyDutyPlan
    template_name = 'profiles/commandant/plans/detail.html'
    context_object_name = 'plan'

    def get_queryset(self):
        return MonthlyDutyPlan.objects.filter(is_generated=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.object
        
        # Получаем все расписания для этого плана
        schedules = DutySchedule.objects.filter(
            date__year=plan.month.year,
            date__month=plan.month.month
        ).select_related('duty', 'assigned_faculty', 'assigned_department')
        
        # Группируем по датам для удобного отображения
        schedules_by_date = defaultdict(list)
        for schedule in schedules:
            schedules_by_date[schedule.date].append(schedule)
        
        # Создаем календарь для отображения
        year = plan.month.year
        month = plan.month.month
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)
        
        calendar_weeks = []
        for week in month_days:
            calendar_week = []
            for day in week:
                if day == 0:
                    calendar_week.append({'day': None, 'date': None, 'schedules': []})
                else:
                    day_date = datetime(year, month, day).date()
                    day_schedules = schedules_by_date.get(day_date, [])
                    calendar_week.append({
                        'day': day,
                        'date': day_date,
                        'schedules': day_schedules,
                        'is_today': day_date == timezone.now().date()
                    })
            calendar_weeks.append(calendar_week)
        
        # Статистика
        unit_stats = defaultdict(lambda: {'count': 0, 'duties': set()})
        for schedule in schedules:
            if schedule.assigned_faculty:
                key = f"faculty_{schedule.assigned_faculty.id}"
                unit_stats[key]['name'] = f"Факультет {schedule.assigned_faculty.name}"
                unit_stats[key]['count'] += 1
                unit_stats[key]['duties'].add(schedule.duty.duty_name)
            elif schedule.assigned_department:
                key = f"department_{schedule.assigned_department.id}"
                unit_stats[key]['name'] = f"Кафедра {schedule.assigned_department.name}"
                unit_stats[key]['count'] += 1
                unit_stats[key]['duties'].add(schedule.duty.duty_name)
        
        # ДОБАВЛЯЕМ ДОСТУПНЫЕ ПОДРАЗДЕЛЕНИЯ ДЛЯ МОДАЛЬНОГО ОКНА
        faculties = Faculty.objects.all()
        independent_departments = Department.objects.filter(faculty__isnull=True)
        
        context.update({
            'schedules': schedules,
            'calendar_weeks': calendar_weeks,
            'unit_stats': dict(unit_stats),
            'total_schedules': schedules.count(),
            'faculties': faculties,
            'independent_departments': independent_departments,
        })
        
        return context


class UpdateScheduleView(IsCommandantMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            schedule_id = kwargs.get('pk')
            unit_type = request.POST.get('unit_type')
            unit_id = request.POST.get('unit_id')
            
            print(f"🔄 Обновление расписания {schedule_id}: {unit_type}_{unit_id}")
            
            schedule = get_object_or_404(DutySchedule, id=schedule_id)
            
            # Сбрасываем предыдущие назначения
            schedule.assigned_faculty = None
            schedule.assigned_department = None
            schedule.assigned_unit_type = None
            
            # Устанавливаем новое назначение
            if unit_type == 'faculty':
                faculty = get_object_or_404(Faculty, id=unit_id)
                schedule.assigned_faculty = faculty
                schedule.assigned_unit_type = 'faculty'
                unit_name = f"Факультет {faculty.name}"
            elif unit_type == 'department':
                department = get_object_or_404(Department, id=unit_id)
                schedule.assigned_department = department
                schedule.assigned_unit_type = 'department'
                unit_name = f"Кафедра {department.name}"
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Неверный тип подразделения'
                })
            
            # Помечаем как измененное вручную
            schedule.is_manually_assigned = True
            schedule.save()
            
            # Получаем обновленный статус
            status = schedule.get_assignment_status()
            
            return JsonResponse({
                'success': True,
                'unit_name': unit_name,
                'schedule_id': schedule_id,
                'status': status,
                'is_manually_assigned': True
            })
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении расписания: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })