from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

class CommandantDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'profiles/commandant/dashboard.html'
    login_url = 'login'
    permission_denied_message = _("У вас недостаточно прав для доступа к этой странице")
    
    def test_func(self):
        """Проверка, что пользователь в группе Кафедра и привязан к кафедре"""
        return True
    
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
        
        # Базовый контекст
        context_data = {
            'user': user,
        }
        
        context.update(context_data)
        return context