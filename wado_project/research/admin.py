# research/admin.py
from django.contrib import admin
from .models import ResearchScenario, EffectivenessReport, SimulationRun

@admin.register(ResearchScenario)
class ResearchScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'n1_scenarios', 'n2_runs', 'created_at']
    list_filter = ['created_at']

@admin.register(EffectivenessReport)
class EffectivenessReportAdmin(admin.ModelAdmin):
    list_display = ['plan', 'scenario', 'p_dc_v1_mean', 'p_dc_v2_mean', 'created_at']
    list_filter = ['created_at', 'scenario']
    search_fields = ['plan__month']

@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    list_display = ['report', 'variant', 'scenario_index', 'run_index', 'is_success']
    list_filter = ['variant', 'is_success']