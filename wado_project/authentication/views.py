# authentication/views.py

from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.views import LogoutView

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')  # или другая страница после выхода

# Вход через CBV
class CustomLoginView(LoginView):
    template_name = 'authentication/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse_lazy('admin:index')
        elif user.groups.filter(name='Комендант').exists():
            return reverse_lazy('commandant:profile')
        elif user.groups.filter(name='Факультет').exists():
            return reverse_lazy('faculty:profile')
        elif user.groups.filter(name='Кафедра').exists():
            return reverse_lazy('department:profile')
        else:
            messages.warning(self.request, 'Вам не назначены права доступа')
            return reverse_lazy('login')


# Выход
def custom_logout_view(request):
    logout(request)
    return redirect('home')


# Редирект после входа
class ProfileRedirectView(TemplateView):
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            return redirect('admin:index')
        elif user.groups.filter(name='Комендант').exists():
            return redirect('commandant:profile')
        elif user.groups.filter(name='Факультет').exists():
            return redirect('faculty:profile')
        elif user.groups.filter(name='Кафедра').exists():
            return redirect('department:profile')
        else:
            messages.warning(request, 'Вам не назначены права доступа')
            return redirect('login')