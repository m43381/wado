from django.urls import path, include
from . import views

app_name = 'commandant'

urlpatterns = [
    path('profile/', views.CommandantDashboardView.as_view(), name='profile'),
    path('duty/', include('duty.urls')),
    path('staff/', views.CommandantStaffListView.as_view(), name='staff'),
    path('staff/<int:pk>/', views.CommandantStaffDetailView.as_view(), name='staff_detail'),
]