from django import forms
from .models import DepartmentMissing

class DepartmentMissingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем классы для всех полей
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'style': 'width: 100%'
            })
        # Специальные настройки для полей даты
        self.fields['start_date'].widget.attrs.update({'type': 'date'})
        self.fields['end_date'].widget.attrs.update({'type': 'date'})
    
    class Meta:
        model = DepartmentMissing
        fields = ['person', 'start_date', 'end_date', 'reason', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }