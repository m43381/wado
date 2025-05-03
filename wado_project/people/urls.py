from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    path('staff/', views.department_staff, name='staff'),
    path('add/', views.add_staff, name='add'),
    path('edit/<int:pk>/', views.edit_staff, name='edit'),
    path('delete/<int:pk>/', views.delete_staff, name='delete'),
]