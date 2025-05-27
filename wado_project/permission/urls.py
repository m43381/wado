# permission/urls.py

from django.urls import path
from . import views

app_name = 'permission'

urlpatterns = [
    # Кафедра
    path('', views.DepartmentPermissionListView.as_view(), name='department_list'),
    path('edit/<int:pk>/', views.DepartmentPermissionEditView.as_view(), name='department_edit'),

    # Факультет
    path('faculty/', views.FacultyPermissionListView.as_view(), name='faculty_list'),
    path('faculty/edit/<int:pk>/', views.FacultyPermissionEditView.as_view(), name='faculty_edit'),
]