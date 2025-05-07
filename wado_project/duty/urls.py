from django.urls import path
from . import views

app_name = 'duty'

urlpatterns = [
    path('', views.duty_list, name='list'),
    path('add/', views.add_duty, name='add'),
    path('edit/<int:pk>/', views.edit_duty, name='edit'),
    path('delete/<int:pk>/', views.delete_duty, name='delete'),
]