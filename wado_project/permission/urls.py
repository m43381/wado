from django.urls import path
from . import views

app_name = 'permission'

urlpatterns = [
    path('', views.DepartmentPermissionListView.as_view(), name='department_list'),
    path('edit/<int:pk>/', views.DepartmentPermissionEditView.as_view(), name='department_edit'),
]