from django.contrib import admin
from .models import Rank

@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ('rank',)  # Поля, отображаемые в списке записей
    search_fields = ('rank',)  # Поля, по которым можно производить поиск
    
    # Настройка отображения названий в админке
    class Meta:
        verbose_name = 'Звание'
        verbose_name_plural = 'Звания'