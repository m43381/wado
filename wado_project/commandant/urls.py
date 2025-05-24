from django.urls import path
from . import views

app_name = 'commandant'

urlpatterns = [
    path('profile/', views.CommandantDashboardView.as_view(), name='profile'),
    path('staff/', views.CommandantStaffListView.as_view(), name='staff'),
    path('staff/<int:pk>/', views.CommandantStaffDetailView.as_view(), name='staff_detail'),
]