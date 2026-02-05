# faculty/models.py
from django.db import models
from django.core.exceptions import ValidationError
from unit.models import Faculty, Department

class FacultyMonthlyPlan(models.Model):
    """Месячный план факультета"""
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        verbose_name='Факультет',
        related_name='faculty_plans'
    )
    month = models.DateField('Месяц планирования')
    
    selected_units = models.JSONField(
        'Выбранные подразделения',
        default=list,
        blank=True,
        help_text='JSON список: ["management"] или ["department_1", "department_2"]'
    )
    
    duty_schedule_settings = models.JSONField(
        'Настройки расписания нарядов',
        default=dict,
        blank=True,
        help_text='JSON с настройками дней для каждого наряда'
    )
    
    is_generated = models.BooleanField('План сгенерирован', default=False)
    last_generated_at = models.DateTimeField('Дата последней генерации', null=True, blank=True)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Факультетский план'
        verbose_name_plural = 'Факультетские планы'
        unique_together = ['faculty', 'month']
        ordering = ['-month']  # ДОБАВЛЕНО: исправляет предупреждение о пагинации
    
    def __str__(self):
        return f"План {self.faculty.name} на {self.month.strftime('%B %Y')}"
    
    def clean(self):
        """Валидация"""
        if self.month.day != 1:
            raise ValidationError('Месяц должен быть первым числом')
    
    def get_duty_schedule(self, duty):
        """Получить настройки расписания для конкретного наряда - ВОЗВРАЩАЕТ ЧИСЛА, НЕ НАЗВАНИЯ"""
        schedule_data = self.duty_schedule_settings.get(str(duty.id), {})
        
        # ВОЗВРАЩАЕМ ТОЧНО ТО, ЧТО ХРАНИТСЯ, без преобразования
        return {
            'ranges': [r for r in schedule_data.get('ranges', []) if r and r.strip()],
            'specific_dates': [d for d in schedule_data.get('specific_dates', []) if d and d.strip()],
            'weekdays': schedule_data.get('weekdays', []),  # Оставляем как есть (числа 0-6)
        }
    
    def get_duty_schedule_display(self, duty):
        """Получить настройки расписания для ОТОБРАЖЕНИЯ в шаблоне"""
        schedule_data = self.duty_schedule_settings.get(str(duty.id), {})
        
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
        raw_weekdays = schedule_data.get('weekdays', [])
        
        for day in raw_weekdays:
            if isinstance(day, str) and day in weekday_names:
                converted_weekdays.append(weekday_names[day])
            elif isinstance(day, int) and str(day) in weekday_names:
                converted_weekdays.append(weekday_names[str(day)])
            elif isinstance(day, str):
                converted_weekdays.append(day)
        
        return {
            'ranges': [r for r in schedule_data.get('ranges', []) if r and r.strip()],
            'specific_dates': [d for d in schedule_data.get('specific_dates', []) if d and d.strip()],
            'weekdays': converted_weekdays,
        }
    
    def set_duty_schedule(self, duty, schedule_data):
        """Установить настройки расписания для наряда"""
        self.duty_schedule_settings[str(duty.id)] = schedule_data
        self.save()
    
    def get_selected_units_display(self):
        """Получить отображение выбранных подразделений"""
        if not self.selected_units:
            return "Не выбраны"
        
        display_list = []
        for unit in self.selected_units:
            if unit == 'management':
                display_list.append("Управление факультета")
            elif unit.startswith('department_'):
                dept_id = unit.replace('department_', '')
                try:
                    department = Department.objects.get(id=dept_id, faculty=self.faculty)
                    display_list.append(f"Кафедра {department.name}")
                except Department.DoesNotExist:
                    display_list.append(f"Кафедра (ID: {dept_id})")
        
        return ", ".join(display_list)