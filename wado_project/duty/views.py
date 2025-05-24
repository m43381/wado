# duty/views.py

from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Duty
from .forms import DutyForm
from core.mixins import (
    LoginRequiredMixin,
    GroupRequiredMixin,
    SuccessMessageMixin,
    BaseDeleteView
)

from django.urls import reverse_lazy


# Список нарядов
class DutyListView(GroupRequiredMixin, ListView):
    model = Duty
    context_object_name = 'dutys'
    template_name = 'profiles/commandant/duty/duty_list.html'
    group_required = ['Комендант']


# Добавление наряда
class DutyCreateView(GroupRequiredMixin, SuccessMessageMixin, CreateView):
    model = Duty
    form_class = DutyForm
    template_name = 'profiles/commandant/duty/add_duty.html'
    success_url = reverse_lazy('commandant:duty:list')
    success_message = 'Наряд успешно добавлен'
    error_message = 'Ошибка при добавлении наряда'
    group_required = ['Комендант']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


# Редактирование наряда
class DutyUpdateView(GroupRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Duty
    form_class = DutyForm
    template_name = 'profiles/commandant/duty/edit_duty.html'
    success_url = reverse_lazy('commandant:duty:list')
    success_message = 'Наряд успешно обновлен'
    error_message = 'Ошибка при редактировании наряда'
    group_required = ['Комендант']


# Удаление наряда
class DutyDeleteView(GroupRequiredMixin, BaseDeleteView):
    model = Duty
    success_url = 'commandant:duty:list'
    success_message = 'Наряд удален'
    error_message = 'Ошибка при удалении наряда'
    group_required = ['Комендант']