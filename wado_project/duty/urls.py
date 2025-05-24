from django.urls import path
from . import views

app_name = 'duty'

urlpatterns = [
    path('', views.DutyListView.as_view(), name='list'),
    path('add/', views.DutyCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', views.DutyUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', views.DutyDeleteView.as_view(), name='delete'),
]