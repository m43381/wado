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

    people_count = models.PositiveIntegerField('Количество людей', default=1)
    
    assigned_faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Закреплённый факультет',
        related_name='assigned_duties_as_faculty'
    )
    assigned_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Закреплённая кафедра',
        related_name='assigned_duties_as_department'
    )

    def __str__(self):
        return self.duty_name

    def get_edit_url(self):
        if self.is_commandant:
            return reverse('commandant:duty:edit', args=[self.pk])
        elif self.faculty and not self.department:
            return reverse('faculty:duty:edit', args=[self.pk])
        elif self.department:
            return reverse('department:duty:edit', args=[self.pk])

    def get_assigned_unit_display(self):
        if self.assigned_faculty:
            return f"Факультет: {self.assigned_faculty.name}"
        elif self.assigned_department:
            return f"Кафедра: {self.assigned_department.name}"
        return "Нет закрепления"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['duty_name'],
                name='unique_duty_for_commandant',
                condition=Q(is_commandant=True)
            ),
            models.UniqueConstraint(
                fields=['duty_name', 'faculty'],
                name='unique_duty_for_faculty',
                condition=Q(faculty__isnull=False, department__isnull=True, is_commandant=False)
            ),
            models.UniqueConstraint(
                fields=['duty_name', 'department'],
                name='unique_duty_for_department',
                condition=Q(department__isnull=False)
            ),
        ]


class DutySchedule(models.Model):
    duty = models.ForeignKey(
        'Duty',
        on_delete=models.CASCADE,
        verbose_name='Наряд',
        related_name='schedules'
    )
    date = models.DateField('Дата наряда')
    
    time_start = models.TimeField(
        'Время начала',
        null=True,
        blank=True,
        help_text='Если не указано, считается на весь день'
    )
    time_end = models.TimeField(
        'Время окончания', 
        null=True,
        blank=True,
        help_text='Если не указано, считается на весь день'
    )
    
    assigned_unit_type = models.CharField(
        'Тип подразделения',
        max_length=20,
        choices=[('faculty', 'Факультет'), ('department', 'Кафедра')],
        null=True,
        blank=True
    )
    assigned_faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Назначенный факультет',
        related_name='assigned_duty_schedules'
    )
    assigned_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Назначенная кафедра',
        related_name='assigned_duty_schedules'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'План наряда'
        verbose_name_plural = 'Планы нарядов'
        unique_together = ['duty', 'date', 'time_start', 'time_end']
        ordering = ['date', 'time_start']

    def __str__(self):
        if self.time_start and self.time_end:
            return f"{self.duty.duty_name} - {self.date.strftime('%d.%m.%Y')} {self.time_start.strftime('%H:%M')}-{self.time_end.strftime('%H:%M')}"
        else:
            return f"{self.duty.duty_name} - {self.date.strftime('%d.%m.%Y')} (весь день)"

    def get_time_display(self):
        """Отображение временного промежутка"""
        if self.time_start and self.time_end:
            return f"{self.time_start.strftime('%H:%M')}-{self.time_end.strftime('%H:%M')}"
        return "Весь день"

    def get_assigned_unit_display(self):
        if self.assigned_faculty:
            return f"Факультет: {self.assigned_faculty.name}"
        elif self.assigned_department:
            return f"Кафедра: {self.assigned_department.name}"
        return "Не назначено"


class MonthlyDutyPlan(models.Model):
    month = models.DateField('Месяц планирования')
    
    duties = models.ManyToManyField(
        'Duty',
        verbose_name='Наряды в плане',
        related_name='monthly_plans',
        through='MonthlyDutyPlanDuty'
    )
    
    is_generated = models.BooleanField('График сгенерирован', default=False)
    duty_schedule_settings = models.JSONField(
        'Настройки расписания нарядов',
        default=dict,
        blank=True,
        help_text='JSON с настройками дней для каждого наряда'
    )
    last_generated_at = models.DateTimeField('Дата последней генерации', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Месячный план нарядов'
        verbose_name_plural = 'Месячные планы нарядов'
        unique_together = ['month']

    def __str__(self):
        return f"План на {self.month.strftime('%B %Y')}"

    def get_duty_schedule(self, duty):
        """Получить настройки расписания для конкретного наряда"""
        schedule_data = self.duty_schedule_settings.get(str(duty.id), {})
        
        # Преобразуем числа дней недели в названия
        weekdays = schedule_data.get('weekdays', [])
        weekday_names = {
            '0': 'Понедельник',
            '1': 'Вторник', 
            '2': 'Среда',
            '3': 'Четверг',
            '4': 'Пятница',
            '5': 'Суббота',
            '6': 'Воскресенье'
        }
        
        converted_weekdays = []
        for day in weekdays:
            if isinstance(day, int):
                day = str(day)
            converted_weekdays.append(weekday_names.get(day, day))
        
        return {
            'ranges': schedule_data.get('ranges', []),
            'specific_dates': schedule_data.get('specific_dates', []),
            'weekdays': converted_weekdays,
        }

    def set_duty_schedule(self, duty, schedule_data):
        """Установить настройки расписания для конкретного наряда"""
        self.duty_schedule_settings[str(duty.id)] = schedule_data
        self.save()

    def clear_duty_schedule(self, duty):
        """Полностью очистить настройки расписания для наряда"""
        if str(duty.id) in self.duty_schedule_settings:
            del self.duty_schedule_settings[str(duty.id)]
            self.save()
            return True
        return False

    def set_duties(self, duties):
        """Установить наряды для плана"""
        self.duties.clear()
        self.duties.add(*duties)
        self.save()

    def add_duty(self, duty):
        """Добавить один наряд в план"""
        self.duties.add(duty)
        self.save()

    def remove_duty(self, duty):
        """Удалить наряд из плана"""
        self.duties.remove(duty)
        self.save()

    def has_duty(self, duty):
        """Проверить, есть ли наряд в плане"""
        return self.duties.filter(id=duty.id).exists()


class MonthlyDutyPlanDuty(models.Model):
    monthly_plan = models.ForeignKey(MonthlyDutyPlan, on_delete=models.CASCADE)
    duty = models.ForeignKey(Duty, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'duty_monthlydutyplan_duties'
        unique_together = ['monthly_plan', 'duty']