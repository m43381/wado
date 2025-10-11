from django.views.generic import TemplateView, FormView, View
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
import calendar
from collections import defaultdict

from core.mixins import IsCommandantMixin
from people.models import People
from unit.models import Faculty, Department
from duty.models import Duty, DutySchedule, MonthlyDutyPlan
from duty.forms import MonthlyPlanForm, DutyScheduleSettingsForm
from duty.services import DutyDistributionService
from missing.models import DepartmentMissing
from permission.models import DepartmentDutyPermission


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
                # Фильтруем пустые значения и некорректные данные по умолчанию
                filtered_schedule = {
                    'ranges': [r for r in schedule_data.get('ranges', []) if r and r.strip()],
                    'specific_dates': [d for d in schedule_data.get('specific_dates', []) if d and d.strip()],
                    'weekdays': [w for w in schedule_data.get('weekdays', []) if w and w.strip() and str(w) not in ['0', '4', '6']],
                }
                duty_schedules[duty.id] = filtered_schedule
        
        # Статистика по подразделениям
        unit_stats = self.get_unit_stats(schedules)
        
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
        })
        
        return context
    
    
    
    def get_unit_stats(self, schedules):
        """Статистика по подразделениям"""
        stats = defaultdict(lambda: {'count': 0, 'duties': set()})
        
        for schedule in schedules:
            if schedule.assigned_faculty:
                key = f"faculty_{schedule.assigned_faculty.id}"
                stats[key]['name'] = f"Факультет {schedule.assigned_faculty.name}"
                stats[key]['count'] += 1
                stats[key]['duties'].add(schedule.duty.duty_name)
            elif schedule.assigned_department:
                key = f"department_{schedule.assigned_department.id}"
                stats[key]['name'] = f"Кафедра {schedule.assigned_department.name}"
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
        
        # Фильтруем пустые значения и очищаем данные
        schedule_data['ranges'] = [r.strip() for r in schedule_data['ranges'] if r and r.strip()]
        schedule_data['specific_dates'] = [d.strip() for d in schedule_data['specific_dates'] if d and d.strip()]
        schedule_data['weekdays'] = [w.strip() for w in schedule_data['weekdays'] if w and w.strip()]
        
        # Получаем текущие настройки
        current_settings = monthly_plan.duty_schedule_settings.copy()
        
        # Если все поля пустые - полностью удаляем настройки для этого наряда
        if not any(schedule_data.values()):
            if str(duty.id) in current_settings:
                del current_settings[str(duty.id)]
                monthly_plan.duty_schedule_settings = current_settings
                monthly_plan.save()
                messages.success(request, f'Настройки расписания для "{duty.duty_name}" полностью очищены')
        else:
            # Сохраняем настройки (только непустые значения)
            current_settings[str(duty.id)] = schedule_data
            monthly_plan.duty_schedule_settings = current_settings
            monthly_plan.save()
            messages.success(request, f'Настройки расписания для "{duty.duty_name}" сохранены')
        
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


class GenerateDutyPlanView(IsCommandantMixin, View):
    def post(self, request, *args, **kwargs):
        year = request.POST.get('year')
        month = request.POST.get('month')
        duty_ids = request.POST.get('duties', '').split(',')
        
        # Убираем пустые значения
        duty_ids = [duty_id for duty_id in duty_ids if duty_id]
        
        try:
            year = int(year)
            month = int(month)
            current_date = datetime(year, month, 1).date()
            
            # Создаем или обновляем месячный план
            monthly_plan, created = MonthlyDutyPlan.objects.get_or_create(
                month=current_date
            )
            
            # Добавляем выбранные наряды
            duties = Duty.objects.filter(id__in=duty_ids)
            monthly_plan.set_duties(duties)
            
            # Генерируем расписание
            distribution_service = DutyDistributionService(current_date)
            schedule_count = distribution_service.generate_schedule(monthly_plan)
            
            messages.success(
                request, 
                f'График нарядов успешно сгенерирован! Создано {schedule_count} записей.'
            )
            
            return JsonResponse({'success': True, 'count': schedule_count})
            
        except Exception as e:
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
                
                # Сбрасываем статус плана
                monthly_plan.is_generated = False
                monthly_plan.last_generated_at = None
                monthly_plan.save()
                
                messages.success(
                    request, 
                    f'График нарядов за {current_date.strftime("%B %Y")} сброшен. Удалено {schedule_count} записей.'
                )
            else:
                messages.info(request, f'План на {current_date.strftime("%B %Y")} не найден')
            
        except Exception as e:
            messages.error(request, f'Ошибка при сбросе графика: {str(e)}')
        
        # Редирект обратно на страницу плана
        redirect_url = reverse('commandant:duty_plan') + f'?year={year}&month={month}'
        return redirect(redirect_url)