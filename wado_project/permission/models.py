from django.db import models
from django.core.exceptions import ValidationError
from people.models import People
from duty.models import Duty

class DepartmentDutyPermission(models.Model):
    """
    Модель для хранения допусков кафедры к нарядам.
    Один человек может быть допущен к одному наряду только один раз.
    """
    person = models.ForeignKey(
        People,
        on_delete=models.CASCADE,
        verbose_name='Человек',
        related_name='department_duty_permissions'
    )
    duty = models.ForeignKey(
        Duty,
        on_delete=models.CASCADE,
        verbose_name='Наряд',
        related_name='department_permitted_persons'
    )
    
    class Meta:
        verbose_name = 'Допуск к наряду (кафедра)'
        verbose_name_plural = 'Допуски к нарядам (кафедра)'
        unique_together = [['person', 'duty']]
        
    def __str__(self):
        return f"{self.person} - {self.duty} (кафедра)"

    def clean(self):
        super().clean()
        # Проверка, что человек принадлежит кафедре
        if not self.person.department:
            raise ValidationError('Человек должен быть привязан к кафедре')
        
        # Проверка на уникальность
        if DepartmentDutyPermission.objects.filter(
            person=self.person, 
            duty=self.duty
        ).exclude(pk=self.pk).exists():
            raise ValidationError('Этот человек уже имеет допуск к данному наряду')


class FacultyDutyPermission(models.Model):
    """
    Модель для хранения допусков факультета к нарядам.
    Один человек может быть допущен к одному наряду только один раз.
    """
    person = models.ForeignKey(
        People,
        on_delete=models.CASCADE,
        verbose_name='Человек',
        related_name='faculty_duty_permissions'
    )
    duty = models.ForeignKey(
        Duty,
        on_delete=models.CASCADE,
        verbose_name='Наряд',
        related_name='faculty_permitted_persons'
    )
    
    class Meta:
        verbose_name = 'Допуск к наряду (факультет)'
        verbose_name_plural = 'Допуски к нарядам (факультет)'
        unique_together = [['person', 'duty']]
        
    def __str__(self):
        return f"{self.person} - {self.duty} (факультет)"

    def clean(self):
        super().clean()
        # Проверка, что человек принадлежит факультету
        if not self.person.faculty:
            raise ValidationError('Человек должен быть привязан к факультету')
            
        # Проверка на уникальность
        if FacultyDutyPermission.objects.filter(
            person=self.person, 
            duty=self.duty
        ).exclude(pk=self.pk).exists():
            raise ValidationError('Этот человек уже имеет допуск к данному наряду')