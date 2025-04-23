from django.contrib import admin
from .models import People

@admin.register(People)
class PeopleAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'faculty',
        'department',
        'rank',
        'last_duty_date',
        'workload'
    )
    list_filter = (
        'faculty',
        'department',
        'rank',
    )
    search_fields = ('full_name',)
    list_select_related = ('faculty', 'department', 'rank')
    list_editable = ('workload',)
    date_hierarchy = 'last_duty_date'
    
    fieldsets = (
        (None, {
            'fields': ('full_name', 'rank')
        }),
        ('Подразделение', {
            'fields': ('faculty', 'department'),
        }),
        ('Рабочие показатели', {
            'fields': ('last_duty_date', 'workload'),
        }),
    )