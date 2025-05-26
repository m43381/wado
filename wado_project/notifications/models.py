# notifications/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_notifications',
        verbose_name="Получатель"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        verbose_name="Отправитель"
    )
    message = models.TextField("Сообщение")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} → {self.recipient}"