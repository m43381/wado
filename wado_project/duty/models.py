from django.db import models
from unit.models import Faculty, Department
from django.urls import reverse
from django.db.models import Q


class Duty(models.Model):
    duty_name = models.CharField('Название наряда', max_length=50)
    duty_weight = models.FloatField('Вес наряда')

    is_commandant = models.BooleanField('Добавлено комендантом', default=False)
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Факультет',
        related_name='duties'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кафедра',
        related_name='duties'
    )

    def get_edit_url(self):
        if self.is_commandant:
            return reverse('commandant:duty:edit', args=[self.pk])
        elif self.faculty and not self.department:
            return reverse('faculty:duty:edit', args=[self.pk])
        elif self.department:
            return reverse('department:duty:edit', args=[self.pk])

    def __str__(self):
        return self.duty_name

    class Meta:
        constraints = [
            # Уникальность для коменданта
            models.UniqueConstraint(
                fields=['duty_name'],
                name='unique_duty_for_commandant',
                condition=Q(is_commandant=True)
            ),
            # Уникальность для факультета
            models.UniqueConstraint(
                fields=['duty_name', 'faculty'],
                name='unique_duty_for_faculty',
                condition=Q(faculty__isnull=False, department__isnull=True, is_commandant=False)
            ),
            # Уникальность для кафедры
            models.UniqueConstraint(
                fields=['duty_name', 'department'],
                name='unique_duty_for_department',
                condition=Q(department__isnull=False)
            ),
        ]