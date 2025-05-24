# people/views.py
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)
from .models import People
from rank.models import Rank
from .forms import PeopleForm
from core.mixins import (
    LoginRequiredMixin,
    HasDepartmentMixin,
    SuccessMessageMixin,
    BaseDeleteView
)
from django.urls import reverse_lazy
from django.urls import reverse
from django.views.generic import ListView


# Список сотрудников
class StaffListView(HasDepartmentMixin, ListView):
    model = People
    context_object_name = 'staff'
    template_name = 'profiles/department/staff/department_staff.html'

    def get_queryset(self):
        return People.objects.filter(department=self.request.user.department).order_by('full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Формируем заголовки таблицы
        headers = [
            {'label': 'ФИО'},
            {'label': 'Звание'},
            {'label': 'Последний наряд'},
            {'label': 'Нагрузка'},
        ]

        # Формируем строки таблицы
        table_items = []
        for person in self.object_list:
            table_items.append({
                'url': reverse('department:people:edit', args=[person.pk]),
                'fields': [
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


from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

class StaffCreateView(LoginRequiredMixin, HasDepartmentMixin, SuccessMessageMixin, CreateView):
    model = People
    form_class = PeopleForm
    template_name = 'profiles/department/staff/add_staff.html'
    success_url = reverse_lazy('department:people:staff')
    success_message = 'Сотрудник успешно добавлен'
    error_message = 'Ошибка при добавлении сотрудника'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.department = self.request.user.department
        form.instance.faculty = self.request.user.faculty
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        # Формируем части формы
        form_parts = []

        # Поле full_name
        full_name_html = render_to_string("components/form_group.html", {
            "field": form['full_name']
        }, request=self.request)
        form_parts.append(full_name_html)

        # Поля rank и last_duty_date в строке
        row_fields = [form['rank'], form['last_duty_date']]
        row_html = render_to_string("components/form_row.html", {
            "fields": row_fields
        }, request=self.request)
        form_parts.append(row_html)

        # Собираем всё вместе
        context.update({
            'form_body': mark_safe('\n'.join(form_parts)),
            'cancel_url': reverse('department:people:staff'),
        })

        return context


# Редактирование сотрудника
class StaffUpdateView(LoginRequiredMixin, HasDepartmentMixin, SuccessMessageMixin, UpdateView):
    model = People
    form_class = PeopleForm
    template_name = 'profiles/department/staff/edit_staff.html'
    success_url = reverse_lazy('department:people:staff')
    success_message = 'Данные сотрудника обновлены'
    error_message = 'Ошибка при редактировании данных'

    def get_queryset(self):
        return People.objects.filter(department=self.request.user.department)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        # Формируем части формы
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
            'cancel_url': reverse('department:people:staff'),
            'delete_url': reverse('department:people:delete', args=[self.object.pk]),
        })

        return context


# Удаление сотрудника
class StaffDeleteView(LoginRequiredMixin, HasDepartmentMixin, DeleteView):
    model = People
    template_name = 'profiles/department/staff/confirm_delete.html'
    success_url = reverse_lazy('department:people:staff')

    def get_queryset(self):
        return People.objects.filter(department=self.request.user.department)