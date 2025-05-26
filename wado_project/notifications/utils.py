# notifications/utils.py

from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

def send_notification(sender, recipient, message):
    Notification.objects.create(
        sender=sender,
        recipient=recipient,
        message=message
    )