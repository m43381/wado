from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from people.models import People
from duty.models import Duty
from .models import DepartmentDutyPermission
from .forms import DepartmentPermissionForm

class DepartmentPermissionListView(LoginRequiredMixin, ListView):
    model = People
    template_name = 'profiles/department/permission/department_permission_list.html'
    context_object_name = 'staff_list'
    
    def get_queryset(self):
        return People.objects.filter(
            department=self.request.user.department
        ).prefetch_related('department_duty_permissions__duty')

class DepartmentPermissionEditView(LoginRequiredMixin, UpdateView):
    model = People
    form_class = DepartmentPermissionForm
    template_name = 'profiles/department/permission/department_permission_edit.html'
    context_object_name = 'person'
    
    def get_success_url(self):
        return reverse_lazy('department:permission:department_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Используем duty_name вместо name для сортировки
        context['duties'] = Duty.objects.all().order_by('duty_name')
        context['current_permissions'] = self.object.department_duty_permissions.values_list('duty_id', flat=True)
        return context