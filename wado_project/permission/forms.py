# permission/forms.py

from django import forms
from people.models import People
from duty.models import Duty
from .models import DepartmentDutyPermission, FacultyDutyPermission


class DepartmentPermissionForm(forms.ModelForm):
    duties = forms.ModelMultipleChoiceField(
        queryset=Duty.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Допуски к нарядам'
    )

    class Meta:
        model = People
        fields = []

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.instance and hasattr(self.instance, 'department_duty_permissions'):
            current_duties = DepartmentDutyPermission.objects.filter(person=self.instance).values_list('duty', flat=True)
            self.fields['duties'].initial = list(current_duties)

        self.fields['duties'].widget.attrs.update({'class': 'custom-duty-checkboxes'})

    def save(self, commit=True):
        person = self.instance
        selected_duties = self.cleaned_data.get('duties', [])

        DepartmentDutyPermission.objects.filter(person=person).delete()
        for duty in selected_duties:
            DepartmentDutyPermission.objects.create(person=person, duty=duty)

        return person


class FacultyPermissionForm(forms.ModelForm):
    duties = forms.ModelMultipleChoiceField(
        queryset=Duty.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Допуски к нарядам (факультет)'
    )

    class Meta:
        model = People
        fields = []

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.instance and hasattr(self.instance, 'faculty_duty_permissions'):
            current_duties = FacultyDutyPermission.objects.filter(person=self.instance).values_list('duty', flat=True)
            self.fields['duties'].initial = list(current_duties)

        self.fields['duties'].widget.attrs.update({'class': 'custom-duty-checkboxes'})

    def save(self, commit=True):
        person = self.instance
        selected_duties = self.cleaned_data.get('duties', [])

        FacultyDutyPermission.objects.filter(person=person).delete()
        for duty in selected_duties:
            FacultyDutyPermission.objects.create(person=person, duty=duty)

        return person