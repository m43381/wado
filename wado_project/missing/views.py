# missing/views.py

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.utils import timezone

from core.mixins import LoginRequiredMixin, HasDepartmentMixin, HasFacultyMixin, SuccessMessageMixin
from people.models import People
from .models import DepartmentMissing, FacultyMissing
from .forms import DepartmentMissingForm, FacultyMissingForm


# Базовый класс для освобождений
class BaseMissingView:
    """
    Базовая логика для освобождений (кафедра / факультет)
    """
    namespace = None  # department / faculty
    related_field = None  # department / faculty
    template_name_prefix = 'profiles/shared/missing/'

    def get_template_names(self):
        return [f"{self.template_name_prefix}{self.template_name_suffix}.html"]

    def get_queryset(self):
        if self.related_field == 'department':
            return self.model.objects.filter(person__department=self.request.user.department).select_related('person')
        elif self.related_field == 'faculty':
            return self.model.objects.filter(person__faculty=self.request.user.faculty).select_related('person')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        object_name = ''
        if self.related_field == 'department':
            object_name = self.request.user.department.name
        elif self.related_field == 'faculty':
            object_name = self.request.user.faculty.name

        context.update({
            'namespace': self.namespace,
            'related_type': self.related_field,
            'related_field': self.related_field,
            'object_name': object_name,
        })
        return context


class BaseMissingListView(BaseMissingView, ListView):
    """
    Список освобождений
    """
    context_object_name = 'missing_list'
    template_name_suffix = '_list'

    def get_queryset(self):
        qs = super().get_queryset()

        filter_type = self.request.GET.get('filter')

        if filter_type == 'active':
            return qs.filter(end_date__gte=timezone.now().date())
        elif filter_type == 'expired':
            return qs.filter(end_date__lt=timezone.now().date())
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        headers = [
            {'label': 'Сотрудник'},
            {'label': 'Период отсутствия'},
            {'label': 'Причина'},
            {'label': 'Статус'},
        ]

        table_items = []
        for record in self.object_list:
            try:
                start = record.start_date.strftime('%d.%m.%Y') if record.start_date else '-'
                end = record.end_date.strftime('%d.%m.%Y') if record.end_date else '-'
                period = f"{start} – {end}"

                status = {
                    'value': 'Активно' if record.is_active else 'Истекло',
                    'class': 'status status-active' if record.is_active else 'status status-expired'
                }

                table_items.append({
                    'url': reverse(f'{self.namespace}:missing:{self.related_field}_edit', args=[record.pk]),
                    'fields': [
                        {'value': record.person.full_name},
                        {'value': period},
                        {'value': record.get_reason_display() or '-'},
                        status,
                    ]
                })
            except Exception as e:
                print(f"Ошибка при построении строки: {e}")

        context.update({
            'headers': headers,
            'table_items': table_items,
        })

        return context


class BaseMissingEditView(BaseMissingView, SuccessMessageMixin, UpdateView):
    """
    Редактирование освобождения
    """
    template_name_suffix = '_edit'

    def get_success_url(self):
        return reverse(f'{self.namespace}:missing:{self.related_field}_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        form_parts = []

        person_html = render_to_string("components/form_group.html", {"field": form['person']}, request=self.request)
        form_parts.append(person_html)

        start_date_html = render_to_string("components/form_group.html", {"field": form['start_date']}, request=self.request)
        form_parts.append(start_date_html)

        end_date_html = render_to_string("components/form_group.html", {"field": form['end_date']}, request=self.request)
        form_parts.append(end_date_html)

        reason_html = render_to_string("components/form_group.html", {"field": form['reason']}, request=self.request)
        form_parts.append(reason_html)

        comment_html = render_to_string("components/form_group.html", {"field": form['comment']}, request=self.request)
        form_parts.append(comment_html)

        delete_url = None
        if self.object and self.object.pk:
            try:
                delete_url = reverse(f'{self.namespace}:missing:{self.related_field}_delete', args=[self.object.pk])
            except:
                delete_url = None

        context.update({
            'form_body': mark_safe('\n'.join(form_parts)),
            'title': 'Редактировать запись об освобождении',
            'icon': 'calendar-edit',
            'cancel_url': reverse(f'{self.namespace}:missing:{self.related_field}_list'),
            'delete_url': delete_url,
        })

        return context


class BaseMissingCreateView(BaseMissingView, SuccessMessageMixin, CreateView):
    """
    Добавление освобождения
    """
    template_name_suffix = '_add'

    def get_success_url(self):
        return reverse(f'{self.namespace}:missing:{self.related_field}_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Форма невалидна:")
        print(form.errors)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        form_parts = []

        person_html = render_to_string("components/form_group.html", {"field": form['person']}, request=self.request)
        form_parts.append(person_html)

        start_date_html = render_to_string("components/form_group.html", {"field": form['start_date']}, request=self.request)
        form_parts.append(start_date_html)

        end_date_html = render_to_string("components/form_group.html", {"field": form['end_date']}, request=self.request)
        form_parts.append(end_date_html)

        reason_html = render_to_string("components/form_group.html", {"field": form['reason']}, request=self.request)
        form_parts.append(reason_html)

        comment_html = render_to_string("components/form_group.html", {"field": form['comment']}, request=self.request)
        form_parts.append(comment_html)

        context.update({
            'form_body': mark_safe('\n'.join(form_parts)),
            'title': 'Добавить запись об освобождении',
            'icon': 'calendar-plus',
            'cancel_url': reverse(f'{self.namespace}:missing:{self.related_field}_list'),
        })

        return context


class BaseMissingDeleteView(BaseMissingView, DeleteView):
    """
    Удаление освобождения
    """
    template_name_suffix = '_confirm_delete'

    def get(self, request, *args, **kwargs):
        """Обрабатываем GET-запрос, чтобы показать подтверждение"""
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(f'{self.namespace}:missing:{self.related_field}_list')


# === Для кафедры ===

class MissingListView(HasDepartmentMixin, BaseMissingListView):
    model = DepartmentMissing
    namespace = 'department'
    related_field = 'department'


class MissingCreateView(HasDepartmentMixin, BaseMissingCreateView):
    model = DepartmentMissing
    form_class = DepartmentMissingForm
    namespace = 'department'
    related_field = 'department'
    success_message = 'Освобождение успешно добавлено'


class MissingUpdateView(HasDepartmentMixin, BaseMissingEditView):
    model = DepartmentMissing
    form_class = DepartmentMissingForm
    namespace = 'department'
    related_field = 'department'
    success_message = 'Освобождение успешно обновлено'


class MissingDeleteView(HasDepartmentMixin, BaseMissingDeleteView):
    model = DepartmentMissing
    namespace = 'department'
    related_field = 'department'


# === Для факультета ===

class FacultyMissingListView(HasFacultyMixin, BaseMissingListView):
    model = FacultyMissing
    namespace = 'faculty'
    related_field = 'faculty'


class FacultyMissingCreateView(HasFacultyMixin, BaseMissingCreateView):
    model = FacultyMissing
    form_class = FacultyMissingForm
    namespace = 'faculty'
    related_field = 'faculty'
    success_message = 'Освобождение успешно добавлено'


class FacultyMissingUpdateView(HasFacultyMixin, BaseMissingEditView):
    model = FacultyMissing
    form_class = FacultyMissingForm
    namespace = 'faculty'
    related_field = 'faculty'
    success_message = 'Освобождение успешно обновлено'


class FacultyMissingDeleteView(HasFacultyMixin, BaseMissingDeleteView):
    model = FacultyMissing
    namespace = 'faculty'
    related_field = 'faculty'