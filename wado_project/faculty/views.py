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
from missing.models import DepartmentMissing, FacultyMissing
from permission.models import DepartmentDutyPermission
from core.mixins import HasFacultyMixin
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Q
from django.db.models import Value, BooleanField


class FacultyStaffView(HasFacultyMixin, TemplateView):
    template_name = 'profiles/faculty/staff/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not hasattr(user, 'faculty') or not user.faculty:
            return context

        department_id = self.request.GET.get('department')
        duty_id = self.request.GET.get('duty')

        from django.db.models import Q, Case, When, Value, BooleanField

        # === Список всех сотрудников: кафедры + управление ===
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

        # === Наряды для выпадающего списка ===
        filtered_duties = Duty.objects.filter(
            Q(is_commandant=True) |
            Q(faculty=user.faculty, department__isnull=True)
        ).distinct()

        # === Кафедры для фильтра ===
        departments = Department.objects.filter(faculty=user.faculty)

        # === Фильтрация по кафедре или наряду ===
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

        today = timezone.now().date()

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