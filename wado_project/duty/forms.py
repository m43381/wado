from django import forms
from .models import Duty

class DutyForm(forms.ModelForm):
    class Meta:
        model = Duty
        fields = ['duty_name', 'duty_weight']
        labels = {
            'duty_name': 'Название наряда',
            'duty_weight': 'Вес наряда'
        }
        widgets = {
            'duty_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название наряда'
            }),
            'duty_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Укажите вес наряда',
                'step': '0.01'
            })
        }
        error_messages = {
            'duty_name': {
                'unique': 'Наряд с таким названием уже существует',
                'required': 'Это поле обязательно для заполнения'
            },
            'duty_weight': {
                'required': 'Это поле обязательно для заполнения',
                'invalid': 'Введите корректное числовое значение'
            }
        }