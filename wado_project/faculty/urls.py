# faculty/urls.py

from django.urls import path, include
from . import views

app_name = 'faculty'

urlpatterns = [
    path('profile/', views.FacultyDashboardView.as_view(), name='profile'),
    path('staff/', views.FacultyStaffView.as_view(), name='staff'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    path('staff/people/', include('people.urls', namespace='people')),
    path('permission/', include('permission.urls', namespace='permission')),
    path('missing/', include('missing.urls', namespace='missing')),
]