from django import forms
from .models import Duty
from unit.models import Faculty, Department
from django.core.exceptions import ValidationError
from datetime import datetime


class DutyForm(forms.ModelForm):
    assigned_type = forms.ChoiceField(
        label='Тип подразделения',
        choices=[
            ('', '---'),
            ('faculty', 'Факультет'),
            ('department', 'Кафедра')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
    )

    assigned_faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        label='Закреплённый факультет',
        required=False,
        empty_label='Не выбрано',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    assigned_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label='Закреплённая кафедра',
        required=False,
        empty_label='Не выбрано',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Применяем классы ко всем полям
        for field_name, field in self.fields.items():
            if field_name not in ['assigned_type', 'assigned_faculty', 'assigned_department']:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off'
                })
                if isinstance(field.widget, forms.DateInput):
                    field.widget.attrs.update({'type': 'date'})

        # Ограничиваем выбор для текущего пользователя
        if self.request and hasattr(self.request, 'user') and self.request.user.is_authenticated:
            user = self.request.user
            if user.department:
                self.fields['assigned_department'].queryset = Department.objects.filter(id=user.department.id)
            elif user.faculty:
                self.fields['assigned_faculty'].queryset = Faculty.objects.filter(id=user.faculty.id)

        # Устанавливаем начальные значения для редактирования
        if self.instance and self.instance.pk:
            if self.instance.assigned_faculty:
                self.initial['assigned_type'] = 'faculty'
                self.fields['assigned_faculty'].initial = self.instance.assigned_faculty
            elif self.instance.assigned_department:
                self.initial['assigned_type'] = 'department'
                self.fields['assigned_department'].initial = self.instance.assigned_department

    class Meta:
        model = Duty
        fields = ['duty_name', 'duty_weight', 'people_count']


    def clean(self):
        cleaned_data = super().clean()
        assigned_type = cleaned_data.get('assigned_type')
        faculty = cleaned_data.get('assigned_faculty')
        department = cleaned_data.get('assigned_department')

        # Если тип не выбран — обнуляем оба поля
        if not assigned_type:
            cleaned_data['assigned_faculty'] = None
            cleaned_data['assigned_department'] = None
        elif assigned_type == 'faculty' and not faculty:
            raise ValidationError({'assigned_faculty': 'Выберите факультет.'})
        elif assigned_type == 'department' and not department:
            raise ValidationError({'assigned_department': 'Выберите кафедру.'})

        return cleaned_data

    def save(self, commit=True):
        duty = super().save(commit=False)
        assigned_type = self.cleaned_data.get('assigned_type')

        if assigned_type == 'faculty':
            duty.assigned_faculty = self.cleaned_data.get('assigned_faculty')
            duty.assigned_department = None
        elif assigned_type == 'department':
            duty.assigned_department = self.cleaned_data.get('assigned_department')
            duty.assigned_faculty = None
        else:
            # Если тип не выбран — обнуляем оба поля
            duty.assigned_faculty = None
            duty.assigned_department = None

        if commit:
            duty.save()
        return duty


class MonthlyPlanForm(forms.Form):
    month = forms.DateField(
        label='Месяц планирования',
        widget=forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
        input_formats=['%Y-%m']
    )
    
    duties = forms.ModelMultipleChoiceField(
        queryset=Duty.objects.filter(is_commandant=True),
        label='Наряды для планирования',
        widget=forms.CheckboxSelectMultiple,
        required=True
    )


class DutyScheduleSettingsForm(forms.Form):
    schedule_type = forms.ChoiceField(
        label='Тип расписания',
        choices=[
            ('all', 'Весь месяц'),
            ('range', 'Диапазон дат'),
            ('specific', 'Конкретные дни'),
            ('weekdays', 'Дни недели')
        ],
        initial='all',
        widget=forms.RadioSelect(attrs={'class': 'schedule-type-radio'})
    )
    
    start_date = forms.DateField(
        label='Начальная дата',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    end_date = forms.DateField(
        label='Конечная дата',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    specific_dates = forms.CharField(
        label='Конкретные даты',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'дд.мм.гггг, дд.мм.гггг...'
        })
    )
    
    weekdays = forms.MultipleChoiceField(
        choices=[
            ('Понедельник', 'Понедельник'),
            ('Вторник', 'Вторник'),
            ('Среда', 'Среда'),
            ('Четверг', 'Четверг'),
            ('Пятница', 'Пятница'),
            ('Суббота', 'Суббота'),
            ('Воскресенье', 'Воскресенье'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Дни недели'
    )

    def clean(self):
        cleaned_data = super().clean()
        schedule_type = cleaned_data.get('schedule_type')
        
        if schedule_type == 'range':
            start_date = cleaned_data.get('start_date')
            end_date = cleaned_data.get('end_date')
            if not start_date or not end_date:
                raise ValidationError('Для диапазона дат укажите начальную и конечную дату')
            if start_date > end_date:
                raise ValidationError('Начальная дата не может быть больше конечной')
                
        elif schedule_type == 'specific':
            specific_dates = cleaned_data.get('specific_dates')
            if not specific_dates:
                raise ValidationError('Укажите конкретные даты')
                
        elif schedule_type == 'weekdays':
            weekdays = cleaned_data.get('weekdays')
            if not weekdays:
                raise ValidationError('Выберите хотя бы один день недели')
        
        return cleaned_data