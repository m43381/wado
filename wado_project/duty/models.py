from django.db import models

# Наряд
class Duty(models.Model):
    duty_name = models.CharField('Название наряда', max_length=50, unique=True)
    duty_weight = models.FloatField('Вес наряда')

    class Meta:
        verbose_name = 'Наряд'
        verbose_name_plural = 'Наряды'
        ordering = ['duty_name']

    def __str__(self):
        return self.duty_name