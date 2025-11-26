from django.urls import path, include
from . import views

app_name = 'commandant'

urlpatterns = [
    path('profile/', views.CommandantDashboardView.as_view(), name='profile'),
    path('duty/', include(('duty.urls_commandant', 'commandant_duty'), namespace='duty')),
    path('staff/', views.CommandantStaffListView.as_view(), name='staff'),
    path('staff/<int:pk>/', views.CommandantStaffDetailView.as_view(), name='staff_detail'),
    path('duty-plan/', views.DutyPlanView.as_view(), name='duty_plan'),
    path('generate-duty-plan/', views.GenerateDutyPlanView.as_view(), name='generate_duty_plan'),
    path('reset-duty-plan/', views.ResetDutyPlanView.as_view(), name='reset_duty_plan'),
    path('plans/', views.PlanListView.as_view(), name='plan_list'),  # НОВЫЙ URL
    path('plans/<int:pk>/', views.PlanDetailView.as_view(), name='plan_detail'),  # Детальный просмотр
    path('schedules/<int:pk>/update/', views.UpdateScheduleView.as_view(), name='update_schedule'),
    
]