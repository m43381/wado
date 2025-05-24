from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    path('staff/', views.StaffListView.as_view(), name='staff'),
    path('add/', views.StaffCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', views.StaffUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', views.StaffDeleteView.as_view(), name='delete'),
]