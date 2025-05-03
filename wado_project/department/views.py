from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.shortcuts import redirect
from people.models import People
from django.db.models import Avg, Count
from django.utils.translation import gettext_lazy as _

class DepartmentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'profiles/department/dashboard.html'
    login_url = 'login'
    permission_denied_message = _("У вас недостаточно прав для доступа к этой странице")
    
    def test_func(self):
        """Проверка, что пользователь в группе Кафедра и привязан к кафедре"""
        return (self.request.user.groups.filter(name='Кафедра').exists() and 
                hasattr(self.request.user, 'department'))
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.warning(self.request, 'Для доступа необходимо авторизоваться')
            return redirect(self.login_url)
        else:
            messages.warning(self.request, 'У вас нет прав доступа к этому разделу')
            return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Получаем статистику по сотрудникам кафедры
        staff_stats = People.objects.filter(
            department=user.department
        ).aggregate(
            total=Count('id'),
            avg_workload=Avg('workload')
        )
        
        # Базовый контекст
        context_data = {
            'user': user,
            'staff_count': staff_stats['total'],
            'avg_workload': round(staff_stats['avg_workload'], 1) if staff_stats['avg_workload'] else 0.0,
            'recent_staff': People.objects.filter(
                department=user.department
            ).order_by('-id')[:5]
        }
        
        # Добавляем кафедру, если она есть
        if hasattr(user, 'department') and user.department:
            context_data['department'] = user.department
        
        # Добавляем факультет, если он есть
        if hasattr(user, 'faculty') and user.faculty:
            context_data['faculty'] = user.faculty
        
        context.update(context_data)
        return context