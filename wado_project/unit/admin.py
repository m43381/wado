from django.contrib import admin
from .models import Faculty, Department


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty')
    list_filter = ('faculty',)
    search_fields = ('name', 'faculty__name')
    ordering = ('name',)
    list_select_related = ('faculty',)
    autocomplete_fields = ('faculty',)