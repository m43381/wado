# people/urls.py

from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    path('', views.PeopleListView.as_view(), name='staff'),
    path('add/', views.PeopleCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', views.PeopleUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', views.PeopleDeleteView.as_view(), name='delete'),
]