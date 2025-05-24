from django.views.generic import TemplateView
from people.models import People
from unit.models import Department
from django.db.models import Count, Avg
from core.mixins import HasFacultyMixin

class FacultyDashboardView(HasFacultyMixin, TemplateView):
    template_name = 'profiles/faculty/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Проверка факультета (уже в HasFacultyMixin)
        if not hasattr(user, 'faculty') or not user.faculty:
            return context

        # Получаем кафедры факультета
        departments = Department.objects.filter(faculty=user.faculty)

        # Базовая статистика
        departments_stats = {
            'total': departments.count(),
            'total_staff': People.objects.filter(department__in=departments).count(),
            'avg_workload': People.objects.filter(department__in=departments).aggregate(Avg('workload'))['workload__avg'] or 0,
        }

        # Топ кафедр
        top_departments = departments.annotate(
            staff_count=Count('people'),
            avg_workload=Avg('people__workload')
        ).order_by('-staff_count')[:5]

        # Добавляем данные в контекст
        context.update({
            'user': user,
            'faculty': user.faculty,
            'departments_count': departments_stats['total'],
            'staff_count': departments_stats['total_staff'],
            'avg_workload': round(departments_stats['avg_workload'], 1),
            'top_departments': top_departments,
        })

        return context
    
# faculty/views.py

from django.views.generic import TemplateView
from people.models import People
from unit.models import Department
from duty.models import Duty
from missing.models import DepartmentMissing
from permission.models import DepartmentDutyPermission
from core.mixins import HasFacultyMixin
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Q


class FacultyStaffView(HasFacultyMixin, TemplateView):
    template_name = 'profiles/faculty/staff/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not hasattr(user, 'faculty') or not user.faculty:
            return context

        # Получаем параметры фильтрации
        department_id = self.request.GET.get('department')
        duty_id = self.request.GET.get('duty')

        # Базовая выборка — все сотрудники факультета
        staff = People.objects.filter(department__faculty=user.faculty).select_related('department', 'rank')

        # Фильтр по кафедре
        departments = Department.objects.filter(faculty=user.faculty)
        if department_id:
            staff = staff.filter(department_id=department_id)

        # Фильтр по допуску к наряду
        if duty_id:
            staff = staff.filter(department_duty_permissions__duty_id=duty_id)

        staff = staff.distinct()

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

            table_items.append({
                'url': reverse('faculty:staff_detail', args=[person.pk]),
                'fields': [
                    {'value': idx},
                    {'value': person.full_name},
                    {'value': str(person.rank) if person.rank else '-'},
                    {'value': str(person.department)},
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
            'faculty': user.faculty,
            'headers': headers,
            'table_items': table_items,
            'departments': departments,
            'duties': Duty.objects.all(),
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