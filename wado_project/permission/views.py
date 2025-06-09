# permission/views.py

from django.views.generic import ListView, UpdateView
from django.urls import reverse, reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin

from core.mixins import HasDepartmentMixin, HasFacultyMixin
from people.models import People
from duty.models import Duty
from .models import DepartmentDutyPermission, FacultyDutyPermission
from .forms import DepartmentPermissionForm, FacultyPermissionForm


class BasePermissionView:
    """
    Общая логика для допусков на уровне кафедры или факультета
    """
    model = People
    template_name_prefix = 'profiles/shared/permission/'
    namespace = None  # department / faculty
    related_field = None  # department / faculty

    def get_template_names(self):
        return [f"{self.template_name_prefix}{self.template_name_suffix}.html"]

    def get_queryset(self):
        if self.related_field == 'department':
            return People.objects.filter(department=self.request.user.department).prefetch_related('department_duty_permissions')
        elif self.related_field == 'faculty':
            return People.objects.filter(faculty=self.request.user.faculty, department__isnull=True).prefetch_related('faculty_duty_permissions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        object_name = ''
        related_type_label = ''

        if self.related_field == 'department' and self.request.user.department:
            object_name = self.request.user.department.name
            related_type_label = 'кафедры'
        elif self.related_field == 'faculty' and self.request.user.faculty:
            object_name = self.request.user.faculty.name
            related_type_label = 'факультета'

        context.update({
            'namespace': self.namespace,
            'related_type': self.related_field,
            'object_name': object_name,
            'related_type_label': related_type_label,
        })
        return context


class PermissionListView(BasePermissionView, ListView):
    """
    Список сотрудников с допусками
    """
    context_object_name = 'staff_list'
    template_name_suffix = '_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        staff_list = []
        for person in self.object_list:
            edit_url = reverse(f'{self.namespace}:permission:{self.related_field}_edit', args=[person.pk])

            if self.related_field == 'department':
                perms = person.department_duty_permissions.all()
            elif self.related_field == 'faculty':
                perms = person.faculty_duty_permissions.all()

            duties = [perm.duty.duty_name for perm in perms] or []

            staff_list.append({
                'url': edit_url,
                'fields': {
                    'full_name': person.full_name,
                    'rank': str(person.rank) if person.rank else '-',
                    'duties': duties,
                }
            })

        add_url = reverse(f'{self.namespace}:people:add')  # убедись, что такой маршрут есть
        print(self.namespace)

        context.update({
            'staff_list': staff_list,
            'add_url': add_url,
        })

        return context


class BasePersonPermissionEditView(SuccessMessageMixin, UpdateView):
    """
    Базовое представление для редактирования допусков через модель People
    """
    model = People
    form_class = None  # будет задан в дочерних классах
    template_name = 'profiles/shared/permission/_edit.html'  # ← УКАЗАН ЯВНО
    namespace = None
    related_field = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse(f'{self.namespace}:permission:{self.related_field}_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.object

        if self.related_field == 'department':
            current_permissions = list(DepartmentDutyPermission.objects.filter(
                person=person
            ).values_list('duty_id', flat=True))
        elif self.related_field == 'faculty':
            current_permissions = list(FacultyDutyPermission.objects.filter(
                person=person
            ).values_list('duty_id', flat=True))

        # Определяем нужные фильтры
        duty_queryset = Duty.objects.none()  # Начинаем с пустого queryset'а
        from django.db.models import Q

        if self.related_field == 'department':
            department = self.request.user.department
            faculty = department.faculty

            duty_queryset = Duty.objects.filter(
                Q(department=department) |  # Кафедральные наряды
                Q(faculty=faculty, department__isnull=True) |  # Факультетские (без кафедры)
                Q(is_commandant=True)  # Комендантские
            )

        elif self.related_field == 'faculty':
            faculty = self.request.user.faculty

            duty_queryset = Duty.objects.filter(
                Q(faculty=faculty, department__isnull=True) |  # Факультетские (без кафедры)
                Q(is_commandant=True)  # Комендантские
            )

        # Формируем список чекбоксов
        duty_checkboxes = []
        for duty in duty_queryset.distinct():
            duty_checkboxes.append({
                'id': duty.id,
                'name': duty.duty_name,
                'checked': 'checked' if duty.id in current_permissions else '',
                'weight': duty.duty_weight,
                'source': 'комендантский' if duty.is_commandant else (
                    'факультетский' if duty.faculty and not duty.department else (
                        'кафедральный' if duty.department else ''
                    )
                )
            })

        context.update({
            'person': person,
            'duty_checkboxes': duty_checkboxes,
            'namespace': self.namespace,
            'related_type': self.related_field,
            'cancel_url': self.get_success_url(),
        })
        return context

# === Для кафедры ===
class DepartmentPermissionListView(HasDepartmentMixin, PermissionListView):
    namespace = 'department'
    related_field = 'department'


class DepartmentPermissionEditView(HasDepartmentMixin, BasePersonPermissionEditView):
    form_class = DepartmentPermissionForm
    success_message = 'Допуски кафедры успешно обновлены'
    namespace = 'department'
    related_field = 'department'


# === Для факультета ===
class FacultyPermissionListView(HasFacultyMixin, PermissionListView):
    namespace = 'faculty'
    related_field = 'faculty'


class FacultyPermissionEditView(HasFacultyMixin, BasePersonPermissionEditView):
    form_class = FacultyPermissionForm
    success_message = 'Допуски факультета успешно обновлены'
    namespace = 'faculty'
    related_field = 'faculty'