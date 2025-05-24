# permission/views.py

from django.views.generic import ListView, UpdateView
from .models import DepartmentDutyPermission
from .forms import DepartmentPermissionForm
from core.mixins import (
    LoginRequiredMixin,
    HasDepartmentMixin,
    SuccessMessageMixin
)
from people.models import People
from duty.models import Duty
from django.urls import reverse_lazy


# Список допусков
class DepartmentPermissionListView(HasDepartmentMixin, ListView):
    model = People
    context_object_name = 'staff_list'
    template_name = 'profiles/department/permission/department_permission_list.html'

    def get_queryset(self):
        return People.objects.filter(department=self.request.user.department).prefetch_related('department_duty_permissions__duty')


# Редактирование допусков
class DepartmentPermissionEditView(HasDepartmentMixin, SuccessMessageMixin, UpdateView):
    model = People
    form_class = DepartmentPermissionForm
    template_name = 'profiles/department/permission/department_permission_edit.html'
    success_url = reverse_lazy('department:permission:department_list')
    success_message = 'Допуски обновлены'
    error_message = 'Ошибка при обновлении допусков'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = self.object
        context['duties'] = Duty.objects.all().order_by('duty_name')
        context['current_permissions'] = self.object.department_duty_permissions.values_list('duty_id', flat=True)
        return context

    def form_valid(self, form):
        form.save()  # ← именно здесь происходит сохранение допусков
        return super().form_valid(form)