from django.urls import path, include
from . import views

app_name = 'commandant'

urlpatterns = [
    path('profile/', views.CommandantDashboardView.as_view(), name='profile'),
    path('duty/', include('duty.urls', namespace='duty'), name='duty'),
]