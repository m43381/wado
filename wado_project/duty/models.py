from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import ValidationError
from unit.models import Faculty, Department
from .utils import normalize_weekday_setting


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

    class Meta:
        verbose_name = 'Наряд'
        verbose_name_plural = 'Наряды'
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

    def __str__(self):
        return self.duty_name

    @property
    def is_fixed_duty(self):
        """Проверить, является ли наряд закрепленным"""
        return bool(self.assigned_faculty or self.assigned_department)
    
    def get_original_assignment(self):
        """Получить исходное закрепленное подразделение"""
        if self.assigned_faculty:
            return ('faculty', self.assigned_faculty)
        elif self.assigned_department:
            return ('department', self.assigned_department)
        return (None, None)

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

    def clean(self):
        """Валидация данных"""
        super().clean()
        
        # Проверка, что назначено только одно подразделение
        if self.assigned_faculty and self.assigned_department:
            raise ValidationError('Нельзя закреплять наряд одновременно за факультетом и кафедрой')
        
        # Проверка, что вес наряда положительный
        if self.duty_weight <= 0:
            raise ValidationError('Вес наряда должен быть положительным числом')
        
        # Проверка количества людей
        if self.people_count <= 0:
            raise ValidationError('Количество людей должно быть положительным числом')


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
    
    is_manually_assigned = models.BooleanField(
        default=False,
        verbose_name='Назначено вручную'
    )
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

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
        """Отображение назначенного подразделения"""
        if self.assigned_faculty:
            return f"Факультет: {self.assigned_faculty.name}"
        elif self.assigned_department:
            return f"Кафедра: {self.assigned_department.name}"
        return "Не назначено"

    def get_assignment_status(self):
        """Получить статус назначения с правильной логикой"""
        # Получаем исходное закрепленное подразделение наряда
        original_unit_type, original_unit = self.duty.get_original_assignment()
        
        print(f"🔍 Анализ статуса для расписания {self.id}:")
        print(f"   - Наряд: {self.duty.duty_name}")
        print(f"   - Исходное закрепление: {original_unit_type} - {original_unit}")
        print(f"   - Назначено: faculty={self.assigned_faculty}, department={self.assigned_department}")
        print(f"   - Ручное назначение: {self.is_manually_assigned}")
        
        # Если наряд закреплен за подразделением
        if original_unit_type and original_unit:
            print("   - Наряд ЗАКРЕПЛЕН за подразделением")
            
            # Проверяем, назначено ли на закрепленное подразделение
            if original_unit_type == 'faculty' and self.assigned_faculty == original_unit:
                print("   - Назначено на ЗАКРЕПЛЕННЫЙ факультет")
                if self.is_manually_assigned:
                    print("   - СТАТУС: Изменен (ручное назначение на правильное подразделение)")
                    return 'changed'
                else:
                    print("   - СТАТУС: Закреплен (автоматическое распределение)")
                    return 'fixed'
                    
            elif original_unit_type == 'department' and self.assigned_department == original_unit:
                print("   - Назначено на ЗАКРЕПЛЕННУЮ кафедру")
                if self.is_manually_assigned:
                    print("   - СТАТУС: Изменен (ручное назначение на правильное подразделение)")
                    return 'changed'
                else:
                    print("   - СТАТУС: Закреплен (автоматическое распределение)")
                    return 'fixed'
            else:
                # Назначено на другое подразделение
                print("   - Назначено на ДРУГОЕ подразделение")
                if self.is_manually_assigned:
                    print("   - СТАТУС: Изменен (ручное назначение на другое подразделение)")
                    return 'changed'
                else:
                    print("   - СТАТУС: Ротация (автоматическое распределение на другое подразделение)")
                    return 'rotating'
                
        else:
            # Для ротационных нарядов (нет закрепленного подразделения)
            print("   - Наряд РОТАЦИОННЫЙ (нет закрепления)")
            if self.is_manually_assigned:
                print("   - СТАТУС: Изменен (ручное назначение)")
                return 'changed'
            else:
                print("   - СТАТУС: Ротация (автоматическое распределение)")
                return 'rotating'
    

    def get_assignment_status_display(self):
        """Текстовое отображение статуса"""
        status = self.get_assignment_status()
        status_map = {
            'fixed': 'Закреплен',
            'rotating': 'Ротация', 
            'changed': 'Изменен'
        }
        return status_map.get(status, 'Неизвестно')

    def get_assignment_badge_class(self):
        """Класс для badge в зависимости от статуса"""
        status = self.get_assignment_status()
        badge_map = {
            'fixed': 'badge-fixed',
            'rotating': 'badge-rotating',
            'changed': 'badge-changed'
        }
        return badge_map.get(status, '')

    def check_manual_assignment(self):
        """Проверить и установить флаг ручного назначения"""
        original_unit_type, original_unit = self.duty.get_original_assignment()
        
        # Если наряд закреплен за подразделением
        if original_unit_type and original_unit:
            # Проверяем, отличается ли назначение от исходного
            if (original_unit_type == 'faculty' and self.assigned_faculty != original_unit) or \
            (original_unit_type == 'department' and self.assigned_department != original_unit):
                return True  # Ручное назначение (изменено)
            else:
                return False # Автоматическое назначение (закреплено)
        else:
            # Для ротационных нарядов любое назначение считается автоматическим
            # если не изменено вручную позже
            return False

    def save(self, *args, **kwargs):
        """Переопределение save для автоматической установки флага ручного назначения"""
        # Если флаг не установлен явно, определяем автоматически
        if self.is_manually_assigned is None:
            self.is_manually_assigned = self.check_manual_assignment()
        
        # Устанавливаем тип подразделения
        if self.assigned_faculty:
            self.assigned_unit_type = 'faculty'
        elif self.assigned_department:
            self.assigned_unit_type = 'department'
        else:
            self.assigned_unit_type = None
        
        super().save(*args, **kwargs)

    @property
    def is_today(self):
        """Проверить, является ли дата сегодняшней"""
        return self.date == timezone.now().date()

    @property
    def is_past(self):
        """Проверить, является ли дата прошедшей"""
        return self.date < timezone.now().date()

    @property
    def is_future(self):
        """Проверить, является ли дата будущей"""
        return self.date > timezone.now().date()

    @property
    def assignment_type(self):
        """Тип назначения (для обратной совместимости)"""
        return self.get_assignment_status()

    def clean(self):
        """Валидация данных"""
        super().clean()
        
        # Проверка, что назначено только одно подразделение
        if self.assigned_faculty and self.assigned_department:
            raise ValidationError('Нельзя назначать одновременно и факультет и кафедру')
        
        # Проверка временного промежутка
        if self.time_start and self.time_end:
            if self.time_start >= self.time_end:
                raise ValidationError('Время начала должно быть раньше времени окончания')

    def get_absolute_url(self):
        """URL для детального просмотра (если нужно)"""
        return reverse('commandant:schedule_detail', kwargs={'pk': self.pk})

    @classmethod
    def get_schedules_for_month(cls, year, month):
        """Получить все расписания для указанного месяца"""
        return cls.objects.filter(
            date__year=year,
            date__month=month
        ).select_related(
            'duty', 
            'assigned_faculty', 
            'assigned_department'
        ).order_by('date', 'time_start')

    @classmethod
    def get_unit_stats(cls, year, month):
        """Статистика по подразделениям за месяц"""
        from collections import defaultdict
        
        schedules = cls.get_schedules_for_month(year, month)
        stats = defaultdict(lambda: {'count': 0, 'duties': set()})
        
        for schedule in schedules:
            if schedule.assigned_faculty:
                key = f"faculty_{schedule.assigned_faculty.id}"
                stats[key]['name'] = f"Факультет {schedule.assigned_faculty.name}"
                stats[key]['count'] += 1
                stats[key]['duties'].add(schedule.duty.duty_name)
            elif schedule.assigned_department:
                key = f"department_{schedule.assigned_department.id}"
                stats[key]['name'] = f"Кафедра {schedule.assigned_department.name}"
                stats[key]['count'] += 1
                stats[key]['duties'].add(schedule.duty.duty_name)
        
        return dict(stats)


class MonthlyDutyPlan(models.Model):
    month = models.DateField('Месяц планирования')
    
    duties = models.ManyToManyField(
        'Duty',
        verbose_name='Наряды в плане',
        related_name='monthly_plans',
        through='MonthlyDutyPlanDuty'
    )
    
    # НОВОЕ ПОЛЕ: выбранные подразделения для распределения
    selected_units = models.JSONField(
        'Выбранные подразделения',
        default=list,
        blank=True,
        help_text='JSON список выбранных подразделений для распределения'
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
        """Получить настройки расписания для конкретного наряда с корректной обработкой дней недели."""
        schedule_data = self.duty_schedule_settings.get(str(duty.id), {})

        # Словарь для отображения дней недели
        weekday_names = {
            0: 'Понедельник',
            1: 'Вторник',
            2: 'Среда',
            3: 'Четверг',
            4: 'Пятница',
            5: 'Суббота',
            6: 'Воскресенье'
        }

        # Нормализуем и преобразуем дни недели
        raw_weekdays = schedule_data.get('weekdays', [])
        converted_weekdays = []
        
        for day in raw_weekdays:
            # Если это уже число (в виде строки), преобразуем
            if isinstance(day, str) and day.isdigit():
                day_num = int(day)
                if 0 <= day_num <= 6:
                    converted_weekdays.append(weekday_names[day_num])
            # Если это число
            elif isinstance(day, int) and 0 <= day <= 6:
                converted_weekdays.append(weekday_names[day])
            # Если это строка с названием, оставляем как есть
            elif isinstance(day, str):
                converted_weekdays.append(day)

        return {
            'ranges': [r for r in schedule_data.get('ranges', []) if r and r.strip()],
            'specific_dates': [d for d in schedule_data.get('specific_dates', []) if d and d.strip()],
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

    def set_selected_units(self, units_data):
        """Установить выбранные подразделения"""
        self.selected_units = units_data
        self.save()

    def get_selected_units_display(self):
        """Получить отображение выбранных подразделений"""
        if not self.selected_units:
            return "Не выбраны"
        
        display_list = []
        for unit in self.selected_units:
            if unit.startswith('faculty_'):
                faculty_id = unit.replace('faculty_', '')
                try:
                    faculty = Faculty.objects.get(id=faculty_id)
                    display_list.append(f"Факультет {faculty.name}")
                except Faculty.DoesNotExist:
                    display_list.append(f"Факультет (ID: {faculty_id})")
            elif unit.startswith('department_'):
                dept_id = unit.replace('department_', '')
                try:
                    department = Department.objects.get(id=dept_id)
                    display_list.append(f"Кафедра {department.name}")
                except Department.DoesNotExist:
                    display_list.append(f"Кафедра (ID: {dept_id})")
        
        return ", ".join(display_list)

    def clean(self):
        """Валидация данных"""
        super().clean()
        
        # Проверка, что месяц указан корректно (первое число месяца)
        if self.month.day != 1:
            raise ValidationError('Месяц планирования должен быть первым числом месяца')


class MonthlyDutyPlanDuty(models.Model):
    monthly_plan = models.ForeignKey(MonthlyDutyPlan, on_delete=models.CASCADE)
    duty = models.ForeignKey(Duty, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'duty_monthlydutyplan_duties'
        unique_together = ['monthly_plan', 'duty']
        verbose_name = 'Наряд в плане'
        verbose_name_plural = 'Наряды в планах'

    def __str__(self):
        return f"{self.duty.duty_name} в плане {self.monthly_plan.month.strftime('%B %Y')}"