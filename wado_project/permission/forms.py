# permission/forms.py

from django import forms
from people.models import People
from duty.models import Duty
from .models import DepartmentDutyPermission


class DepartmentPermissionForm(forms.ModelForm):
    duties = forms.ModelMultipleChoiceField(
        queryset=Duty.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Допуски к нарядам'
    )

    class Meta:
        model = People
        fields = []  # так как мы редактируем только допуски через отдельное поле

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.instance and hasattr(self.instance, 'department_duty_permissions'):
            current_duties = DepartmentDutyPermission.objects.filter(person=self.instance).values_list('duty', flat=True)
            self.fields['duties'].initial = list(current_duties)

        # Убираем заголовки "Выберите" из ManyToMany
        self.fields['duties'].widget.attrs.update({
            'class': 'custom-duty-checkboxes'
        })

    def save(self, commit=True):
        person = self.instance
        
        # Получаем новые допуски из формы
        selected_duties = self.cleaned_data.get('duties', [])

        # Удаляем старые допуски
        DepartmentDutyPermission.objects.filter(person=person).delete()

        # Создаём новые
        for duty in selected_duties:
            DepartmentDutyPermission.objects.create(person=person, duty=duty)

        return person