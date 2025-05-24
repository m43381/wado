# missing/forms.py

from django import forms
from .models import DepartmentMissing
from people.models import People
from django.forms import DateInput


class DepartmentMissingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Ограничиваем выбор сотрудников по кафедре пользователя
        if self.request and hasattr(self.request.user, 'department'):
            self.fields['person'].queryset = People.objects.filter(
                department=self.request.user.department
            )

        # Применяем стили ко всем полям
        for field_name, field in self.fields.items():
            if field_name == 'reason':
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name == 'person':
                field.widget.attrs.update({'class': 'form-control select2'})
            elif field_name in ['start_date', 'end_date']:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'type': 'text'  # ← изменено здесь
                })
            else:
                field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = DepartmentMissing
        fields = ['person', 'start_date', 'end_date', 'reason', 'comment']
        widgets = {
            'reason': forms.Select(),
            'person': forms.Select(),  # можно заменить на Select2Widget
            'comment': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'person': 'Сотрудник',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
            'reason': 'Причина',
            'comment': 'Комментарий',
        }