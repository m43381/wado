from django.urls import path
from . import views

app_name = 'faculty'

urlpatterns = [
    path('profile/', views.FacultyDashboardView.as_view(), name='profile'),
]