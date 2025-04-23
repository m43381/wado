from django.contrib import admin
from .models import FacultyMissing, DepartmentMissing

@admin.register(FacultyMissing)
class FacultyMissingAdmin(admin.ModelAdmin):
    list_display = ('person', 'start_date', 'end_date', 'reason', 'get_duration_days')
    list_filter = ('reason', 'start_date')
    search_fields = ('person__full_name', 'comment')
    date_hierarchy = 'start_date'
    fieldsets = (
        (None, {
            'fields': ('person', ('start_date', 'end_date'))
        }),
        ('Детали', {
            'fields': ('reason', 'comment')
        }),
    )

    def get_duration_days(self, obj):
        return (obj.end_date - obj.start_date).days
    get_duration_days.short_description = 'Дней'
    get_duration_days.admin_order_field = 'end_date'

@admin.register(DepartmentMissing)
class DepartmentMissingAdmin(admin.ModelAdmin):
    list_display = ('person', 'start_date', 'end_date', 'reason', 'get_duration_days')
    list_filter = ('reason', 'start_date')
    search_fields = ('person__full_name', 'comment')
    date_hierarchy = 'start_date'
    fieldsets = (
        (None, {
            'fields': ('person', ('start_date', 'end_date'))
        }),
        ('Детали', {
            'fields': ('reason', 'comment')
        }),
    )

    def get_duration_days(self, obj):
        return (obj.end_date - obj.start_date).days
    get_duration_days.short_description = 'Дней'
    get_duration_days.admin_order_field = 'end_date'