from django.urls import path
from . import views

app_name = 'faculty'

urlpatterns = [
    path('profile/', views.FacultyDashboardView.as_view(), name='profile'),
    path('staff/', views.FacultyStaffView.as_view(), name='staff'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
]