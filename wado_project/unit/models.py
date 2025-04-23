from django.db import models


# Модель факультета
class Faculty(models.Model):
    name = models.CharField(max_length=20, verbose_name="Название факультета", unique=True)
    
    class Meta:
        verbose_name = 'Факультет'
        verbose_name_plural = 'Факультеты'
    
    def __str__(self):
        return self.name
    
# Модель кафедры
class Department(models.Model):
    name = models.CharField(max_length=20, verbose_name="Название кафедры", unique=True)
    faculty = models.ForeignKey(
        'Faculty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Факультет",
        related_name="departments"
    )
    
    class Meta:
        verbose_name = 'Кафедра'
        verbose_name_plural = 'Кафедры'
    
    def __str__(self):
        if self.faculty:
            return f"{self.name} ({self.faculty})"
        return self.name