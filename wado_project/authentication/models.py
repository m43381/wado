from django.db import models
from django.contrib.auth.models import AbstractUser 
from unit.models import Faculty, Department

class CustomUser (AbstractUser ):
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Факультет",
        related_name="users"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Кафедра",
        related_name="users"
    )
    
    # Переопределяем поля groups и user_permissions
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # Уникальное имя для обратного доступа
        blank=True,
        help_text='Группы, к которым принадлежит этот пользователь.',
        verbose_name='Группы'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # Уникальное имя для обратного доступа
        blank=True,
        help_text='Конкретные разрешения для этого пользователя.',
        verbose_name='Разрешения пользователя'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.username