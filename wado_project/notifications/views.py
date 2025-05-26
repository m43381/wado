# notifications/views.py

from django.views.generic import ListView, CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from .models import Notification
from .forms import NotificationForm
from django.shortcuts import redirect
from django.views.generic import View

User = get_user_model()


from django.http import JsonResponse

def mark_all_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return JsonResponse({'status': 'ok', 'unread_count': 0})

from django.utils import timezone

class NotificationListView(TemplateView):
    template_name = 'notifications/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем все полученные сообщения
        received = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

        # Помечаем непрочитанные как прочитанные
        unread = received.filter(is_read=False)
        unread.update(is_read=True)

        # Передаём в шаблон
        context['notifications'] = {
            'received': received,
            'sent': Notification.objects.filter(sender=self.request.user).order_by('-created_at')
        }

        context['unread_count'] = received.filter(is_read=False).count()  # Всегда 0 после обновления

        return context


class SendNotificationView(CreateView):
    model = Notification
    form_class = NotificationForm
    template_name = 'notifications/send.html'
    success_url = reverse_lazy('notifications:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.sender = self.request.user
        return super().form_valid(form)


class SentNotificationsView(TemplateView):
    template_name = 'notifications/sent.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notifications'] = Notification.objects.filter(sender=self.request.user).order_by('-created_at')
        return context
    
class ClearNotificationsView(View):
    def post(self, request, *args, **kwargs):
        # Очистка всех уведомлений (можно разделить на received/sent при необходимости)
        Notification.objects.filter(recipient=request.user).delete()
        return redirect('notifications:list')