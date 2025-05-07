from django import forms
from .models import DepartmentMissing
from django.forms.widgets import DateInput  # Импортируем виджет DateInput

class DepartmentMissingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем классы для всех полей
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'style': 'width: 100%'
            })
    
    class Meta:
        model = DepartmentMissing
        fields = ['person', 'start_date', 'end_date', 'reason', 'comment']
        widgets = {
            'start_date': DateInput(attrs={'type': 'date'}),  # Используем DateInput с type='date'
            'end_date': DateInput(attrs={'type': 'date'}),   # для полей даты
            'comment': forms.Textarea(attrs={'rows': 3}),
        }