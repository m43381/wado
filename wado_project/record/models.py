from django.db import models
from django.core.exceptions import ValidationError
from people.models import People
from duty.models import Duty

class DutyRecord(models.Model):
    """
    Модель записи на наряд.
    Один человек не может быть записан на один и тот же наряд на одну дату дважды.
    """
    duty = models.ForeignKey(
        Duty,
        on_delete=models.CASCADE,
        verbose_name='Наряд',
        related_name='records'
    )
    date = models.DateField(
        verbose_name='Дата наряда'
    )
    person = models.ForeignKey(
        People,
        on_delete=models.CASCADE,
        verbose_name='Человек',
        related_name='duty_records'
    )
    
    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        unique_together = [['duty', 'date', 'person']]
        ordering = ['date', 'duty']
        
    def __str__(self):
        return f"{self.person} - {self.duty} ({self.date})"

    def clean(self):
        super().clean()
        
        # Проверка уникальности
        if DutyRecord.objects.filter(
            duty=self.duty,
            date=self.date,
            person=self.person
        ).exclude(pk=self.pk).exists():
            raise ValidationError('Этот человек уже записан на этот наряд на указанную дату')