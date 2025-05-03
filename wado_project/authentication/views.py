from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages

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
            messages.warning(self.request, 'Ваш аккаунт не имеет назначенных прав доступа')
            return reverse_lazy('login')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

@login_required
def profile_redirect(request):
    if request.user.is_superuser:
        return redirect('admin:index')
    elif request.user.groups.filter(name='Комендант').exists():
        return redirect('commandant:profile')
    elif request.user.groups.filter(name='Факультет').exists():
        return redirect('faculty:profile')
    elif request.user.groups.filter(name='Кафедра').exists():
        return redirect('department:profile')
    else:
        messages.warning(request, 'Ваш аккаунт не имеет назначенных прав доступа')
        return redirect('login')