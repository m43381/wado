# people/views.py

from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from .models import People
from .forms import PeopleForm

from core.mixins import LoginRequiredMixin
from missing.models import DepartmentMissing


class BasePeopleView:
    """
    Базовый класс для работы с сотрудниками.
    Автоматически определяет уровень доступа: кафедра или факультет.
    """
    model = People
    form_class = PeopleForm
    template_name_prefix = 'profiles/shared/people/'

    def get_template_names(self):
        return [f"{self.template_name_prefix}{self.template_name_suffix}.html"]

    def get_related_type(self):
        """Определяет, от имени какого подразделения действует пользователь"""
        if self.request.user.department:
            return 'department'
        elif self.request.user.faculty:
            return 'faculty'
        raise PermissionDenied("У вас нет прав для управления сотрудниками")

    def get_queryset(self):
        related_type = self.get_related_type()
        if related_type == 'department':
            return People.objects.filter(department=self.request.user.department)
        elif related_type == 'faculty':
            return People.objects.filter(faculty=self.request.user.faculty, department__isnull=True)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_type = self.get_related_type()
        object_name = ''
        if related_type == 'department':
            object_name = self.request.user.department.name
        else:
            object_name = self.request.user.faculty.name

        context.update({
            'related_type': related_type,
            'object_name': object_name,
        })

        return context

    def form_valid(self, form):
        related_type = self.get_related_type()
        if related_type == 'department':
            form.instance.department = self.request.user.department
            form.instance.faculty = self.request.user.faculty
        elif related_type == 'faculty':
            form.instance.faculty = self.request.user.faculty
            form.instance.department = None
        return super().form_valid(form)


class PeopleListView(BasePeopleView, ListView):
    context_object_name = 'staff'
    template_name_suffix = '_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем текущий namespace (например, 'faculty:people')
        current_namespace = self.request.resolver_match.namespace

        related_type = self.get_related_type()
        context['add_url'] = reverse(f'{current_namespace}:add')
        context['related_type_label'] = 'кафедры' if related_type == 'department' else 'факультета'

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

            edit_url = reverse(f'{current_namespace}:edit', args=[person.pk])

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

    def get_success_url(self):
        current_namespace = self.request.resolver_match.namespace
        return reverse(f'{current_namespace}:staff')

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

    def get_success_url(self):
        current_namespace = self.request.resolver_match.namespace
        return reverse(f'{current_namespace}:staff')

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

        delete_url = reverse(f"{self.request.resolver_match.namespace}:delete", args=[self.object.pk])

        context.update({
            'form_body': mark_safe('\n'.join(form_parts)),
            'cancel_url': self.get_success_url(),
            'delete_url': delete_url,
        })

        return context


class PeopleDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = People
    template_name = 'profiles/shared/people/_confirm_delete.html'
    success_message = 'Сотрудник успешно удалён'

    def get_success_url(self):
        current_namespace = self.request.resolver_match.namespace
        return reverse(f'{current_namespace}:staff')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.get_success_url()
        return context