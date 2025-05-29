# missing/forms.py

from django import forms
from .models import DepartmentMissing, FacultyMissing
from people.models import People
from django.utils import timezone


class DepartmentMissingForm(forms.ModelForm):
    class Meta:
        model = DepartmentMissing
        fields = ['person', 'start_date', 'end_date', 'reason', 'comment']
        widgets = {
            'reason': forms.Select(),
            'person': forms.Select(),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'person': 'Сотрудник',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
            'reason': 'Причина',
            'comment': 'Комментарий',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request.user, 'department'):
            self.fields['person'].queryset = People.objects.filter(
                department=self.request.user.department
            )

        for field_name, field in self.fields.items():
            if field_name == 'reason':
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name == 'person':
                field.widget.attrs.update({'class': 'form-control select2'})
            elif field_name in ['start_date', 'end_date']:
                field.widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', "Дата окончания не может быть раньше даты начала")

        today = timezone.now().date()
        if end_date and end_date < today:
            self.add_error('end_date', "Нельзя указывать дату окончания в прошлом")

        return cleaned_data


class FacultyMissingForm(forms.ModelForm):
    class Meta:
        model = FacultyMissing
        fields = ['person', 'start_date', 'end_date', 'reason', 'comment']
        widgets = {
            'reason': forms.Select(),
            'person': forms.Select(),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'person': 'Сотрудник',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
            'reason': 'Причина',
            'comment': 'Комментарий',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and hasattr(self.request.user, 'faculty'):
            self.fields['person'].queryset = People.objects.filter(
                faculty=self.request.user.faculty,
                department__isnull=True
            )

        for field_name, field in self.fields.items():
            if field_name == 'reason':
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name == 'person':
                field.widget.attrs.update({'class': 'form-control select2'})
            elif field_name in ['start_date', 'end_date']:
                field.widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', "Дата окончания не может быть раньше даты начала")

        today = timezone.now().date()
        if end_date and end_date < today:
            self.add_error('end_date', "Нельзя указывать дату окончания в прошлом")

        return cleaned_data