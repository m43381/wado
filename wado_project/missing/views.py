# missing/views.py

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from .models import DepartmentMissing
from .forms import DepartmentMissingForm

from core.mixins import HasDepartmentMixin, LoginRequiredMixin, SuccessMessageMixin, BaseDeleteView


# Список освобождений
class MissingListView(HasDepartmentMixin, ListView):
    model = DepartmentMissing
    context_object_name = 'missing_list'
    template_name = 'profiles/department/missing/department_missing_list.html'

    def get_queryset(self):
        return DepartmentMissing.objects.filter(
            person__department=self.request.user.department
        ).select_related('person')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        headers = [
            {'label': 'Сотрудник'},
            {'label': 'Период отсутствия'},
            {'label': 'Причина'},
        ]

        table_items = []
        for record in self.object_list:
            period = f"{record.start_date.strftime('%d.%m.%Y')} – {record.end_date.strftime('%d.%m.%Y')}" if record.start_date and record.end_date else '-'

            table_items.append({
                'url': reverse('department:missing:department_edit', args=[record.pk]),
                'fields': [
                    {'value': record.person.full_name},
                    {'value': period},
                    {'value': record.get_reason_display() or '-'},
                ]
            })

        context.update({
            'headers': headers,
            'table_items': table_items,
        })

        return context


# Добавление освобождения
class MissingCreateView(LoginRequiredMixin, HasDepartmentMixin, SuccessMessageMixin, CreateView):
    model = DepartmentMissing
    form_class = DepartmentMissingForm
    template_name = 'profiles/department/missing/department_missing_add.html'
    success_url = reverse_lazy('department:missing:department_list')
    success_message = 'Освобождение успешно добавлено'
    error_message = 'Ошибка при добавлении освобождения'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        # Формируем части формы
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
            'cancel_url': reverse('department:missing:department_list'),
        })

        return context


# Редактирование освобождения
class MissingUpdateView(LoginRequiredMixin, HasDepartmentMixin, SuccessMessageMixin, UpdateView):
    model = DepartmentMissing
    form_class = DepartmentMissingForm
    template_name = 'profiles/department/missing/department_missing_edit.html'
    success_url = reverse_lazy('department:missing:department_list')
    success_message = 'Освобождение обновлено'
    error_message = 'Ошибка при редактировании освобождения'

    def get_queryset(self):
        return DepartmentMissing.objects.filter(person__department=self.request.user.department)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        # Формируем части формы
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
                delete_url = reverse('department:missing:department_delete', args=[self.object.pk])
            except:
                delete_url = None

        context.update({
            'form_body': mark_safe('\n'.join(form_parts)),
            'title': 'Редактировать запись об освобождении',
            'icon': 'calendar-edit',
            'cancel_url': reverse('department:missing:department_list'),
            'delete_url': delete_url,
        })

        return context


# Удаление освобождения
class MissingDeleteView(HasDepartmentMixin, DeleteView):
    model = DepartmentMissing
    template_name = 'profiles/department/missing/confirm_delete.html'
    success_url = reverse_lazy('department:missing:department_list')

    def get_queryset(self):
        # Убедись, что объект принадлежит кафедре пользователя
        return DepartmentMissing.objects.filter(person__department=self.request.user.department)

    def delete(self, request, *args, **kwargs):
        print("Метод delete вызван")
        return super().delete(request, *args, **kwargs)