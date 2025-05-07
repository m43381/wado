from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from people.models import People
from django.db.models import Count, Avg, Sum
from unit.models import Department

class FacultyDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'profiles/faculty/dashboard.html'
    login_url = 'login'
    permission_denied_message = _("У вас недостаточно прав для доступа к этой странице")
    
    def test_func(self):
        """Проверка, что пользователь в группе Факультет и привязан к факультету"""
        return (self.request.user.groups.filter(name='Факультет').exists() and 
                hasattr(self.request.user, 'faculty'))
    
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
        
        if not hasattr(user, 'faculty') or not user.faculty:
            return context
        
        # Получаем кафедры факультета
        departments = Department.objects.filter(faculty=user.faculty)
        
        # Получаем статистику по кафедрам
        departments_stats = {
            'total': departments.count(),
            'total_staff': People.objects.filter(department__in=departments).count(),
            'avg_workload': People.objects.filter(
                department__in=departments
            ).aggregate(avg=Avg('workload'))['avg'] or 0
        }
        
        # Получаем список кафедр с количеством сотрудников и средней нагрузкой
        annotated_departments = departments.annotate(
            staff_count=Count('people'),
            avg_workload=Avg('people__workload')
        ).order_by('-staff_count')[:5]
        
        # Базовый контекст
        context.update({
            'user': user,
            'faculty': user.faculty,
            'departments_count': departments_stats['total'],
            'staff_count': departments_stats['total_staff'],
            'avg_workload': round(departments_stats['avg_workload'], 1),
            'top_departments': annotated_departments
        })
        
        return context