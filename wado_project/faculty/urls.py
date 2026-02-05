# faculty/urls.py - добавляем URL для удаления
from django.urls import path, include
from . import views

app_name = 'faculty'

urlpatterns = [
    # Основные страницы
    path('profile/', views.FacultyDashboardView.as_view(), name='profile'),
    path('staff/', views.FacultyStaffView.as_view(), name='staff'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    
    # Планировщик факультетских нарядов
    path('duty/plan/', views.FacultyDutyPlanView.as_view(), name='duty_plan'),
    path('duty/plan/generate/', views.GenerateFacultyPlanView.as_view(), name='generate_duty_plan'),
    path('duty/plan/reset/', views.ResetFacultyPlanView.as_view(), name='reset_duty_plan'),
    path('duty/plan/list/', views.FacultyPlanListView.as_view(), name='plan_list'),
    path('duty/plan/<int:pk>/', views.FacultyPlanDetailView.as_view(), name='plan_detail'),
    path('duty/plan/<int:pk>/delete/', views.DeleteFacultyPlanView.as_view(), name='delete_plan'),  # ДОБАВЛЕНО
    
    # Редактирование назначений
    path('schedules/<int:pk>/update/', views.UpdateFacultyScheduleView.as_view(), name='update_schedule'),
    
    # Академические наряды (распределенные комендантом)
    path('academic-duties/', views.FacultyAcademicDutiesView.as_view(), name='academic_duties'),
    
    # Включение других приложений
    path('people/', include(('people.urls', 'people'), namespace='people')),
    path('permission/', include('permission.urls', namespace='permission')),
    path('missing/', include('missing.urls', namespace='missing')),
    path('duty/', include(('duty.urls_faculty', 'faculty_duty'), namespace='duty')),
]