from django.db import models

# Звание
class Rank(models.Model):
    rank = models.CharField('Звание', max_length=30, unique=True)

    class Meta:
        verbose_name = 'Звание'
        verbose_name_plural = 'Звания'

    def __str__(self):
        return self.rank