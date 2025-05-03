from django import forms
from .models import People
from rank.models import Rank

class PeopleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Настраиваем поля
        self.fields['rank'].queryset = Rank.objects.all()
        self.fields['last_duty_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
        
        # Удаляем ненужные поля, если они есть в форме
        for field_name in ['faculty', 'department', 'workload']:
            if field_name in self.fields:
                del self.fields[field_name]
        
        # Добавляем классы для оставшихся полей
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })
            if field_name == 'last_duty_date':
                field.widget.attrs['placeholder'] = 'дд.мм.гггг'

    class Meta:
        model = People
        fields = ['full_name', 'rank', 'last_duty_date']
        labels = {
            'full_name': 'Полное имя',
            'rank': 'Звание',
            'last_duty_date': 'Дата последнего наряда'
        }