from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.contrib.messages.views import SuccessMessageMixin as DjangoSuccessMessageMixin
from .models import Duty
from .forms import DutyForm

from core.mixins import (
    LoginRequiredMixin,
    GroupRequiredMixin,
    HasFacultyMixin,
    HasDepartmentMixin,
    BaseDeleteView,
    SuccessMessageMixin,
)

from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)


class BaseDutyView:
    """
    Базовый класс для всех действий с нарядами
    """
    model = Duty
    form_class = DutyForm
    template_name_prefix = 'profiles/shared/duty/'
    namespace = None  # commandant / faculty / department
    related_field = None  # commandant / faculty / department

    def get_template_names(self):
        return [f"{self.template_name_prefix}{self.template_name_suffix}.html"]

    def get_queryset(self):
        user = self.request.user
        queryset = None

        if self.related_field == 'commandant':
            queryset = Duty.objects.filter(is_commandant=True)
        elif self.related_field == 'faculty':
            queryset = Duty.objects.filter(
                faculty=user.faculty,
                department__isnull=True,
                is_commandant=False
            )
        elif self.related_field == 'department':
            queryset = Duty.objects.filter(
                department=user.department,
                is_commandant=False
            )
        else:
            queryset = Duty.objects.none()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        object_name = ''
        if self.related_field == 'commandant':
            object_name = 'Коменданта'
        elif self.related_field == 'faculty' and self.request.user.faculty:
            object_name = self.request.user.faculty.name
        elif self.related_field == 'department' and self.request.user.department:
            object_name = self.request.user.department.name

        context.update({
            'namespace': self.namespace,
            'related_type': self.related_field,
            'object_name': object_name,
        })
        return context

    def get_success_url(self):
        return reverse(f'{self.namespace}:duty:list')


# === СПИСОК НАРЯДОВ ===

class DutyListView(BaseDutyView, ListView):
    context_object_name = 'duties'
    template_name_suffix = '_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['add_url'] = reverse(f'{self.namespace}:duty:add')
        return context


# === ДОБАВЛЕНИЕ НАРЯДА ===

class DutyCreateView(
    BaseDutyView,
    LoginRequiredMixin,
    GroupRequiredMixin,
    SuccessMessageMixin,
    CreateView
):
    template_name_suffix = '_add'
    success_message = 'Наряд успешно добавлен'
    error_message = 'Ошибка при добавлении наряда'

    def form_valid(self, form):
        user = self.request.user

        if self.related_field == 'commandant':
            form.instance.is_commandant = True
        elif self.related_field == 'faculty':
            form.instance.faculty = user.faculty
            form.instance.department = None
            form.instance.is_commandant = False
        elif self.related_field == 'department':
            form.instance.department = user.department
            form.instance.faculty = None
            form.instance.is_commandant = False

        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        name_html = render_to_string("components/form_group.html", {"field": form['duty_name']}, request=self.request)
        weight_html = render_to_string("components/form_group.html", {"field": form['duty_weight']}, request=self.request)

        context.update({
            'form_body': mark_safe('\n'.join([name_html, weight_html])),
            'cancel_url': self.get_success_url(),
        })

        return context


# === РЕДАКТИРОВАНИЕ НАРЯДА ===

class DutyUpdateView(
    BaseDutyView,
    LoginRequiredMixin,
    GroupRequiredMixin,
    SuccessMessageMixin,
    UpdateView
):
    template_name_suffix = '_edit'
    success_message = 'Наряд успешно обновлен'
    error_message = 'Ошибка при редактировании наряда'

    def dispatch(self, request, *args, **kwargs):
        duty = self.get_object()
        user = request.user

        # Проверяем права на редактирование
        if duty.is_commandant and not user.groups.filter(name='Комендант').exists():
            messages.warning(request, "Вы не можете редактировать наряд коменданта")
            return redirect(f'{self.namespace}:duty:list')

        if duty.faculty and duty.faculty != user.faculty:
            messages.warning(request, "Вы не можете редактировать чужой наряд")
            return redirect(f'{self.namespace}:duty:list')

        if duty.department and duty.department != user.department:
            messages.warning(request, "Вы не можете редактировать чужой наряд")
            return redirect(f'{self.namespace}:duty:list')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        name_html = render_to_string("components/form_group.html", {"field": form['duty_name']}, request=self.request)
        weight_html = render_to_string("components/form_group.html", {"field": form['duty_weight']}, request=self.request)

        delete_url = reverse(f'{self.namespace}:duty:delete', args=[self.object.pk])

        context.update({
            'form_body': mark_safe('\n'.join([name_html, weight_html])),
            'cancel_url': self.get_success_url(),
            'delete_url': delete_url,
        })

        return context


# === УДАЛЕНИЕ НАРЯДА ===


class DutyDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Duty
    template_name = 'profiles/shared/duty/confirm_delete.html'
    context_object_name = 'object'  # для шаблона confirm_delete.html
    success_message = 'Наряд успешно удалён'
    error_message = 'Ошибка при удалении наряда'

    def get_success_url(self):
        return reverse_lazy(f'{self.namespace}:duty:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.get_success_url()
        return context

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            messages.success(request, self.success_message)
            return response
        except Exception as e:
            messages.error(request, self.error_message + f': {str(e)}')
            return redirect(self.get_success_url())


# === КОНКРЕТНЫЕ ПРЕДСТАВЛЕНИЯ ===

# Комендант
class CommandantDutyListView(DutyListView):
    related_field = 'commandant'
    namespace = 'commandant'
    group_required = ['Комендант']


class CommandantDutyCreateView(DutyCreateView):
    related_field = 'commandant'
    namespace = 'commandant'
    group_required = ['Комендант']


class CommandantDutyUpdateView(DutyUpdateView):
    related_field = 'commandant'
    namespace = 'commandant'
    group_required = ['Комендант']


class CommandantDutyDeleteView(DutyDeleteView):
    related_field = 'commandant'
    namespace = 'commandant'
    group_required = ['Комендант']


# Факультет
class FacultyDutyListView(DutyListView, HasFacultyMixin):
    related_field = 'faculty'
    namespace = 'faculty'


class FacultyDutyCreateView(DutyCreateView, HasFacultyMixin):
    related_field = 'faculty'
    namespace = 'faculty'
    group_required = ['Факультет']


class FacultyDutyUpdateView(DutyUpdateView, HasFacultyMixin):
    related_field = 'faculty'
    namespace = 'faculty'
    group_required = ['Факультет']


class FacultyDutyDeleteView(DutyDeleteView, HasFacultyMixin):
    related_field = 'faculty'
    namespace = 'faculty'
    group_required = ['Факультет']


# Кафедра
class DepartmentDutyListView(DutyListView, HasDepartmentMixin):
    related_field = 'department'
    namespace = 'department'
    group_required = ['Кафедра']


class DepartmentDutyCreateView(DutyCreateView, HasDepartmentMixin):
    related_field = 'department'
    namespace = 'department'
    group_required = ['Кафедра']


class DepartmentDutyUpdateView(DutyUpdateView, HasDepartmentMixin):
    related_field = 'department'
    namespace = 'department'
    group_required = ['Кафедра']


class DepartmentDutyDeleteView(DutyDeleteView, HasDepartmentMixin):
    related_field = 'department'
    namespace = 'department'
    group_required = ['Кафедра']