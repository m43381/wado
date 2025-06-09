# profiles/commandant/views.py

from django.views.generic import TemplateView
from core.mixins import IsCommandantMixin


class CommandantDashboardView(IsCommandantMixin, TemplateView):
    template_name = 'profiles/commandant/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Базовый контекст
        context.update({
            'user': user,
        })

        return context
    
# profiles/commandant/views.py

from django.views.generic import TemplateView
from people.models import People
from unit.models import Faculty, Department
from duty.models import Duty
from missing.models import DepartmentMissing
from permission.models import DepartmentDutyPermission
from core.mixins import IsCommandantMixin
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count


class CommandantStaffListView(IsCommandantMixin, TemplateView):
    template_name = 'profiles/commandant/staff/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем параметры фильтрации
        unit_id = self.request.GET.get('unit')  # может быть id факультета или кафедры
        duty_id = self.request.GET.get('duty')

        # Формируем список доступных подразделений:
        # - только факультеты
        # - и кафедры БЕЗ факультета
        faculties = Faculty.objects.annotate(
            staff_count=Count('departments__people')
        ).order_by('name')

        departments_without_faculty = Department.objects.filter(faculty__isnull=True).annotate(
            staff_count=Count('people')
        ).order_by('name')

        units = []

        # Добавляем факультеты с постфиксом "(факультет)"
        for f in faculties:
            unit_entry = {
                'type': 'faculty',
                'id': f'id_f_{f.id}',
                'name': f'{f.name} факультет',
                'staff_count': f.staff_count,
                'is_selected': f'id_f_{f.id}' == unit_id,
            }
            units.append(unit_entry)

        # Добавляем кафедры без факультета с постфиксом "(кафедра)"
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
                # Выводим сотрудников:
                # 1. всех кафедр этого факультета
                # 2. людей, прикреплённых к этому факультету, но без кафедры
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