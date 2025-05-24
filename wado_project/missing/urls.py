from django.urls import path
from . import views

app_name = 'missing'

urlpatterns = [
    path('', views.MissingListView.as_view(), name='department_list'),
    path('add/', views.MissingCreateView.as_view(), name='department_add'),
    path('edit/<int:pk>/', views.MissingUpdateView.as_view(), name='department_edit'),
    path('delete/<int:pk>/', views.MissingDeleteView.as_view(), name='department_delete'),
]