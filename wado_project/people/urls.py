# people/urls.py

from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    # Кафедра
    path('', views.DepartmentPeopleListView.as_view(), name='staff'),
    path('add/', views.DepartmentPeopleCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', views.DepartmentPeopleUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', views.DepartmentPeopleDeleteView.as_view(), name='delete'),

    # Факультет
    path('faculty/', views.FacultyPeopleListView.as_view(), name='faculty_staff'),
    path('faculty/add/', views.FacultyPeopleCreateView.as_view(), name='faculty_add'),
    path('faculty/edit/<int:pk>/', views.FacultyPeopleUpdateView.as_view(), name='faculty_edit'),
    path('faculty/delete/<int:pk>/', views.FacultyPeopleDeleteView.as_view(), name='faculty_delete'),
]