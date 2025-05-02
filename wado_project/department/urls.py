from django.urls import path
from . import views

app_name = 'department'

urlpatterns = [
    path('', views.DepartmentDashboardView.as_view(), name='dashboard'),
    # Другие URL для кафедры
]