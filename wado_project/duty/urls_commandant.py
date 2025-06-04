from django.urls import path
from duty import views

app_name = 'commandant_duty'

urlpatterns = [
    path('', views.CommandantDutyListView.as_view(), name='list'),
    path('add/', views.CommandantDutyCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', views.CommandantDutyUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', views.CommandantDutyDeleteView.as_view(), name='delete'),
]