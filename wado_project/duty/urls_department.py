from django.urls import path
from duty import views

app_name = 'department_duty'

urlpatterns = [
    path('', views.DepartmentDutyListView.as_view(), name='list'),
    path('add/', views.DepartmentDutyCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', views.DepartmentDutyUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', views.DepartmentDutyDeleteView.as_view(), name='delete'),
]