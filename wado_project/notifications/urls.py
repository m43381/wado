# urls.py

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('send/', views.SendNotificationView.as_view(), name='send'),
    path('sent/', views.SentNotificationsView.as_view(), name='sent'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('clear/', views.ClearNotificationsView.as_view(), name='clear'),
]