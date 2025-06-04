# duty/forms.py

from django import forms
from .models import Duty
from django.core.exceptions import ValidationError


class DutyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Извлекаем request, если он передан
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Применяем классы ко всем полям
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })

            # Можно дополнительно уточнить для определённых типов полей
            if isinstance(field.widget, forms.widgets.DateInput):
                field.widget.attrs.update({'type': 'date'})

    class Meta:
        model = Duty
        fields = ['duty_name', 'duty_weight']

    def clean(self):
        cleaned_data = super().clean()
        duty_name = cleaned_data.get('duty_name')

        if not duty_name:
            raise ValidationError({'duty_name': 'Это обязательное поле'})

        # Получаем текущий объект (при создании instance.pk = None)
        instance = getattr(self, 'instance', None)

        is_commandant = getattr(instance, 'is_commandant', False)
        faculty = getattr(instance, 'faculty', None)
        department = getattr(instance, 'department', None)

        # Если мы в форме создания, то related_field берём из URL
        if not instance.pk and hasattr(self, 'request'):
            user = self.request.user
            if user.department:
                department = user.department
                faculty = None
                is_commandant = False
            elif user.faculty:
                faculty = user.faculty
                department = None
                is_commandant = False
            elif self.request.user.groups.filter(name='Комендант').exists():
                is_commandant = True
                faculty = None
                department = None

        # Проверяем уникальность внутри группы
        if is_commandant:
            if Duty.objects.filter(duty_name=duty_name, is_commandant=True).exclude(pk=instance.pk if instance else None).exists():
                raise ValidationError({
                    'duty_name': 'Наряд с таким названием уже существует у команданта'
                })

        elif faculty and not department:
            if Duty.objects.filter(duty_name=duty_name, faculty=faculty).exclude(pk=instance.pk if instance else None).exists():
                raise ValidationError({
                    'duty_name': f'Наряд с таким названием уже существует на факультете "{faculty}"'
                })

        elif department:
            if Duty.objects.filter(duty_name=duty_name, department=department).exclude(pk=instance.pk if instance else None).exists():
                raise ValidationError({
                    'duty_name': f'Наряд с таким названием уже существует на кафедре "{department}"'
                })

        return cleaned_data