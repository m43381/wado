from django.contrib import admin
from .models import Duty

@admin.register(Duty)
class DutyAdmin(admin.ModelAdmin):
    # Поля, отображаемые в списке
    list_display = ('duty_name', 'duty_weight')
    
    # Поля, по которым можно искать
    search_fields = ('duty_name',)
    
    # Поля, по которым можно фильтровать
    list_filter = ('duty_weight',)
    
    # Поля, которые можно редактировать прямо из списка
    list_editable = ('duty_weight',)
    
    # Поля, по которым можно кликать для перехода к редактированию
    list_display_links = ('duty_name',)
    
    # Автоматическое заполнение slug (если бы было такое поле)
    # prepopulated_fields = {'slug': ('duty_name',)}
    
    # Настройки для формы редактирования
    fieldsets = (
        (None, {
            'fields': ('duty_name', 'duty_weight')
        }),
    )

    class Meta:
        verbose_name = 'Наряд'
        verbose_name_plural = 'Наряды'