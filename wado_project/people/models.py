from django.db import models
from unit.models import Faculty, Department
from rank.models import Rank


class People(models.Model):
    full_name = models.CharField('ФИО', max_length=100)
    faculty = models.ForeignKey(
        Faculty,
        verbose_name='Факультет',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        Department,
        verbose_name='Кафедра',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    rank = models.ForeignKey(
        Rank,
        verbose_name='Звание',
        on_delete=models.PROTECT
    )
    last_duty_date = models.DateField(
        'Дата последнего наряда',
        null=True,
        blank=True
    )
    workload = models.FloatField(
        'Нагрузка',
        default=0.0
    )

    class Meta:
        verbose_name = 'Человек'
        verbose_name_plural = 'Люди'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name