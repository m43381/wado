from django.urls import path
from duty import views

app_name = 'faculty_duty'

urlpatterns = [
    path('', views.FacultyDutyListView.as_view(), name='list'),
    path('add/', views.FacultyDutyCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', views.FacultyDutyUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', views.FacultyDutyDeleteView.as_view(), name='delete'),
]