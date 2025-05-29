# missing/models.py

from django.db import models
from django.utils import timezone
from people.models import People


class MissingReason(models.TextChoices):
    ILLNESS = 'illness', 'Болезнь'
    BUSINESS_TRIP = 'business_trip', 'Командировка'
    VACATION = 'vacation', 'Отпуск'
    OTHER = 'other', 'Другое'


class FacultyMissing(models.Model):
    person = models.ForeignKey(People, on_delete=models.CASCADE, related_name='faculty_missing')
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания')
    reason = models.CharField('Причина', max_length=50, choices=MissingReason.choices, default=MissingReason.ILLNESS)
    comment = models.TextField('Комментарий', blank=True, null=True)

    class Meta:
        verbose_name = 'Освобождение от факультета'
        verbose_name_plural = 'Освобождения от факультетов'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.person} - {self.get_reason_display()} ({self.start_date} – {self.end_date})"

    @property
    def is_active(self):
        return self.end_date >= timezone.now().date()
    
class DepartmentMissing(models.Model):
    person = models.ForeignKey(People, on_delete=models.CASCADE, related_name='department_missing')
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания')
    reason = models.CharField('Причина', max_length=50, choices=MissingReason.choices, default=MissingReason.ILLNESS)
    comment = models.TextField('Комментарий', blank=True, null=True)

    class Meta:
        verbose_name = 'Освобождение от кафедры'
        verbose_name_plural = 'Освобождения от кафедр'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.person} - {self.get_reason_display()} ({self.start_date} – {self.end_date})"

    @property
    def is_active(self):
        return self.end_date >= timezone.now().date()