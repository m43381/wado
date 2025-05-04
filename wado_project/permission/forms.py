from django import forms
from people.models import People
from duty.models import Duty
from .models import DepartmentDutyPermission

class DepartmentPermissionForm(forms.ModelForm):
    duties = forms.ModelMultipleChoiceField(
        queryset=Duty.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Доступные наряды"
    )
    
    class Meta:
        model = People
        fields = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs:
            # Используем duty_name вместо name для сортировки
            self.fields['duties'].queryset = Duty.objects.all().order_by('duty_name')
            self.fields['duties'].initial = kwargs['instance'].department_duty_permissions.values_list('duty_id', flat=True)
    
    def save(self, commit=True):
        person = super().save(commit=False)
        if commit:
            person.save()
            person.department_duty_permissions.all().delete()
            for duty in self.cleaned_data['duties']:
                DepartmentDutyPermission.objects.create(person=person, duty=duty)
        return person