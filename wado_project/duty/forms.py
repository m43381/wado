# duty/forms.py

from django import forms
from .models import Duty

class DutyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # ← здесь забираем request
        super().__init__(*args, **kwargs)

    class Meta:
        model = Duty
        fields = ['duty_name', 'duty_weight']
        labels = {
            'duty_name': 'Название наряда',
            'duty_weight': 'Вес наряда'
        }
        widgets = {
            'duty_name': forms.TextInput(attrs={'class': 'form-control'}),
            'duty_weight': forms.NumberInput(attrs={'class': 'form-control'})
        }
        error_messages = {
            'duty_name': {'unique': 'Наряд с таким названием уже существует'},
        }