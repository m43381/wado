from django.contrib import admin
from .models import DutyRecord

@admin.register(DutyRecord)
class DutyRecordAdmin(admin.ModelAdmin):
    list_display = ('person', 'duty', 'date')
    list_filter = ('date', 'duty', 'person__department')
    search_fields = ('person__last_name', 'person__first_name', 'duty__name')
    date_hierarchy = 'date'
    raw_id_fields = ('person', 'duty')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('person', 'duty')