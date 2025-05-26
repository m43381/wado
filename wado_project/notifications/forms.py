# notifications/forms.py

from django import forms
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


def get_recipients(user):
    if hasattr(user, 'department') and user.department:
        return User.objects.filter(groups__name='Факультет').exclude(pk=user.pk)

    elif hasattr(user, 'faculty') and user.faculty:
        depts = User.objects.filter(department__faculty=user.faculty)
        commandants = User.objects.filter(groups__name='Комендант')
        return depts | commandants

    elif user.groups.filter(name='Комендант').exists():
        faculties = User.objects.filter(groups__name='Факультет')
        independent_depts = User.objects.filter(department__faculty__isnull=True)
        return faculties | independent_depts

    return User.objects.none()


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['recipient', 'message']
        labels = {
            'recipient': 'Получатель',
            'message': 'Сообщение'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['recipient'].queryset = get_recipients(self.user).distinct()