from django.urls import path
from . import views

app_name = 'missing'

urlpatterns = [
    path('', views.department_missing_list, name='department_list'),
    path('add/', views.department_missing_add, name='department_add'),
    path('edit/<int:pk>/', views.department_missing_edit, name='department_edit'),
    path('delete/<int:pk>/', views.department_missing_delete, name='department_delete'),
]