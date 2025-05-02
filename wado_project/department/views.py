from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.shortcuts import redirect

class DepartmentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'profiles/department/dashboard.html'
    
    def test_func(self):
        """Проверка, что пользователь в группе Кафедра"""
        return self.request.user.groups.filter(name='Кафедра').exists()
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.warning(self.request, 'Для доступа необходимо авторизоваться')
            return redirect('login')
        else:
            messages.warning(self.request, 'У вас нет прав доступа к этому разделу')
            return redirect('home')