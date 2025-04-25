from django.contrib import admin
from .models import DepartmentDutyPermission, FacultyDutyPermission

@admin.register(DepartmentDutyPermission)
class DepartmentDutyPermissionAdmin(admin.ModelAdmin):
    list_display = ('person', 'duty')
    list_filter = ('duty', 'person__department')
    search_fields = ('person__last_name', 'person__first_name', 'duty__name')
    raw_id_fields = ('person', 'duty')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('person', 'duty')

@admin.register(FacultyDutyPermission)
class FacultyDutyPermissionAdmin(admin.ModelAdmin):
    list_display = ('person', 'duty')
    list_filter = ('duty', 'person__faculty')
    search_fields = ('person__last_name', 'person__first_name', 'duty__name')
    raw_id_fields = ('person', 'duty')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('person', 'duty')