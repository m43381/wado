# core/mixins.py

from django.contrib.auth.mixins import LoginRequiredMixin as DjangoLoginRequiredMixin
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.views.generic.base import ContextMixin, View
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


class HasDepartmentMixin(DjangoLoginRequiredMixin):
    login_url = 'login'
    permission_denied_message = _("У вас недостаточно прав для доступа к этому разделу")
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, _("Для доступа необходимо войти"))
            return redirect(self.login_url)
        
        if not request.user.groups.filter(name='Кафедра').exists():
            messages.error(request, _("Вы не состоите в группе Кафедра"))
            return redirect('home')

        if not hasattr(request.user, 'department') or not request.user.department:
            messages.warning(request, _("У вас не назначена кафедра"))
            return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)
    
# Миксин: Проверка авторизации
class LoginRequiredMixin(DjangoLoginRequiredMixin):
    login_url = 'login'

    def get_login_redirect(self):
        return redirect(self.login_url)


# Миксин: Пользователь должен быть привязан к кафедре
class HasDepartmentMixin:
    """Проверяет, что у пользователя есть кафедра"""
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'department') or not request.user.department:
            messages.warning(request, "У вас нет прав доступа к этому разделу")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


# Миксин: Пользователь должен быть привязан к факультету
class HasFacultyMixin:
    """Проверяет, что у пользователя есть факультет"""
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'faculty') or not request.user.faculty:
            messages.warning(request, "У вас нет прав доступа к этому разделу")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


# Миксин: Пользователь должен состоять в определённой группе
class GroupRequiredMixin:
    """
    Проверяет, что пользователь состоит в одной из указанных групп.
    
    Пример использования:
        group_required = ['Комендант', 'Факультет']
    """
    group_required = None

    def dispatch(self, request, *args, **kwargs):
        if self.group_required is None:
            raise NotImplementedError("Необходимо указать группы в group_required")

        user_groups = set(request.user.groups.values_list('name', flat=True))
        required_groups = set(self.group_required)

        if not (user_groups & required_groups):
            messages.warning(request, "Недостаточно прав для доступа")
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)


# Миксин: Добавляет сообщения об успехе/ошибке
class SuccessMessageMixin:
    success_message = ""
    error_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.error_message:
            messages.error(self.request, self.error_message)
        return response


# Базовый класс для удаления с подтверждением
class BaseDeleteView(LoginRequiredMixin, View):
    model = None
    template_name = 'confirm_delete.html'
    success_url = ''
    success_message = 'Запись успешно удалена'
    error_message = 'Ошибка при удалении'

    def get_object(self):
        obj = self.model.objects.filter(pk=self.kwargs['pk']).first()
        if not obj:
            raise PermissionDenied("Объект не найден")
        return obj

    def get_success_url(self):
        return reverse_lazy(self.success_url)

    def post(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            obj.delete()
            messages.success(request, self.success_message)
        except Exception as e:
            messages.error(request, self.error_message or str(e))
        return redirect(self.get_success_url())