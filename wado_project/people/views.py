# people/views.py

from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone

from .models import People
from .forms import PeopleForm

from core.mixins import (
    LoginRequiredMixin,
    HasFacultyMixin,
    HasDepartmentMixin,
)

from missing.models import DepartmentMissing


class BasePeopleView:
    """
    Базовый класс с общей логикой для кафедры и факультета
    """
    model = People
    form_class = PeopleForm
    template_name_prefix = 'profiles/shared/people/'
    namespace = None  # department / faculty
    related_field = None  # department / faculty

    def get_template_names(self):
        return [f"{self.template_name_prefix}{self.template_name_suffix}.html"]

    def get_queryset(self):
        if self.related_field == 'department':
            return People.objects.filter(department=self.request.user.department)
        elif self.related_field == 'faculty':
            return People.objects.filter(faculty=self.request.user.faculty, department__isnull=True)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Приоритет: сначала кафедра, потом факультет
        object_name = ''
        if self.request.user.department:
            object_name = self.request.user.department.name
        elif self.request.user.faculty:
            object_name = self.request.user.faculty.name

        context.update({
            'namespace': self.namespace,
            'related_type': self.related_field,
            'object_name': object_name,
        })

        return context

    def form_valid(self, form):
        if self.related_field == 'department':
            form.instance.department = self.request.user.department
            form.instance.faculty = self.request.user.faculty
        elif self.related_field == 'faculty':
            form.instance.faculty = self.request.user.faculty
            form.instance.department = None
        return super().form_valid(form)


# people/views.py

class PeopleListView(BasePeopleView, ListView):
    context_object_name = 'staff'
    template_name_suffix = '_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # URL для добавления
        if self.related_field == 'department':
            context['add_url'] = reverse(f'{self.namespace}:people:add')
        elif self.related_field == 'faculty':
            context['add_url'] = reverse(f'{self.namespace}:people:faculty_add')

        # Подпись: кафедры / факультета
        context['related_type_label'] = {
            'department': 'кафедры',
            'faculty': 'факультета'
        }.get(self.related_field, '')

        headers = [
            {'label': '#'},
            {'label': 'ФИО'},
            {'label': 'Звание'},
            {'label': 'Последний наряд'},
            {'label': 'Нагрузка'},
        ]

        today = timezone.now().date()
        table_items = []
        for idx, person in enumerate(self.object_list, start=1):
            missing = DepartmentMissing.objects.filter(
                person=person,
                start_date__lte=today,
                end_date__gte=today
            ).first()

            missing_info = '-'
            if missing:
                missing_info = f"{missing.get_reason_display()} ({missing.start_date.strftime('%d.%m')} – {missing.end_date.strftime('%d.%m')})"

            # Формируем URL редактирования
            if self.related_field == 'department':
                edit_url = reverse(f'{self.namespace}:people:edit', args=[person.pk])
            elif self.related_field == 'faculty':
                edit_url = reverse(f'{self.namespace}:people:faculty_edit', args=[person.pk])

            table_items.append({
                'url': edit_url,
                'fields': [
                    {'value': idx},
                    {'value': person.full_name},
                    {'value': str(person.rank) if person.rank else '-'},
                    {'value': person.last_duty_date.strftime('%d.%m.%Y') if person.last_duty_date else '-'},
                    {'value': f"{person.workload}"},
                ]
            })

        context.update({
            'headers': headers,
            'table_items': table_items,
        })

        return context


class PeopleCreateView(BasePeopleView, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name_suffix = '_add'
    success_message = 'Сотрудник успешно добавлен'
    error_message = 'Ошибка при добавлении сотрудника'

    def get_success_url(self):
        if self.related_field == 'department':
            return reverse(f'{self.namespace}:people:staff')
        elif self.related_field == 'faculty':
            return reverse(f'{self.namespace}:people:faculty_staff')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        # Генерация HTML-формы через компоненты
        form_parts = []

        full_name_html = render_to_string("components/form_group.html", {
            "field": form['full_name']
        }, request=self.request)
        form_parts.append(full_name_html)

        row_fields = [form['rank'], form['last_duty_date']]
        row_html = render_to_string("components/form_row.html", {
            "fields": row_fields
        }, request=self.request)
        form_parts.append(row_html)

        context.update({
            'form_body': mark_safe('\n'.join(form_parts)),
            'cancel_url': self.get_success_url(),
        })

        return context


class PeopleUpdateView(BasePeopleView, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name_suffix = '_edit'
    success_message = 'Данные сотрудника обновлены'
    error_message = 'Ошибка при редактировании данных'

    def get_success_url(self):
        if self.related_field == 'department':
            return reverse(f'{self.namespace}:people:staff')
        elif self.related_field == 'faculty':
            return reverse(f'{self.namespace}:people:faculty_staff')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        form_parts = []

        full_name_html = render_to_string("components/form_group.html", {
            "field": form['full_name']
        }, request=self.request)
        form_parts.append(full_name_html)

        row_fields = [form['rank'], form['last_duty_date']]
        row_html = render_to_string("components/form_row.html", {
            "fields": row_fields
        }, request=self.request)
        form_parts.append(row_html)

        delete_url = ''
        if self.related_field == 'department':
            delete_url = reverse(f'{self.namespace}:people:delete', args=[self.object.pk])
        elif self.related_field == 'faculty':
            delete_url = reverse(f'{self.namespace}:people:faculty_delete', args=[self.object.pk])

        context.update({
            'form_body': mark_safe('\n'.join(form_parts)),
            'cancel_url': self.get_success_url(),
            'delete_url': delete_url,
        })

        return context


class PeopleDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = People
    context_object_name = 'object'
    template_name = 'profiles/shared/people/confirm_delete.html'

    def get_success_url(self):
        if self.related_field == 'department':
            return reverse(f'{self.namespace}:people:staff')
        elif self.related_field == 'faculty':
            return reverse(f'{self.namespace}:people:faculty_staff')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.get_success_url()
        return context


# === Для кафедры ===
class DepartmentPeopleListView(PeopleListView):
    namespace = 'department'
    related_field = 'department'


class DepartmentPeopleCreateView(PeopleCreateView):
    namespace = 'department'
    related_field = 'department'


class DepartmentPeopleUpdateView(PeopleUpdateView):
    namespace = 'department'
    related_field = 'department'


class DepartmentPeopleDeleteView(PeopleDeleteView):
    namespace = 'department'
    related_field = 'department'


# === Для факультета ===
class FacultyPeopleListView(PeopleListView):
    namespace = 'faculty'
    related_field = 'faculty'


class FacultyPeopleCreateView(PeopleCreateView):
    namespace = 'faculty'
    related_field = 'faculty'


class FacultyPeopleUpdateView(PeopleUpdateView):
    namespace = 'faculty'
    related_field = 'faculty'


class FacultyPeopleDeleteView(PeopleDeleteView):
    namespace = 'faculty'
    related_field = 'faculty'