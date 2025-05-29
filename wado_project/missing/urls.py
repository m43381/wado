# missing/urls.py

from django.urls import path
from . import views

app_name = 'missing'

urlpatterns = [
    # Для кафедры
    path('', views.MissingListView.as_view(), name='department_list'),
    path('add/', views.MissingCreateView.as_view(), name='department_add'),
    path('edit/<int:pk>/', views.MissingUpdateView.as_view(), name='department_edit'),
    path('delete/<int:pk>/', views.MissingDeleteView.as_view(), name='department_delete'),

    # Для факультета
    path('faculty/', views.FacultyMissingListView.as_view(), name='faculty_list'),
    path('faculty/add/', views.FacultyMissingCreateView.as_view(), name='faculty_add'),
    path('faculty/edit/<int:pk>/', views.FacultyMissingUpdateView.as_view(), name='faculty_edit'),
    path('faculty/delete/<int:pk>/', views.FacultyMissingDeleteView.as_view(), name='faculty_delete'),
]