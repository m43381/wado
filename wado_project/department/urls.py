from django.urls import path, include
from . import views

app_name = 'department'

urlpatterns = [
    path('profile/', views.DepartmentDashboardView.as_view(), name='profile'),
    path('people/', include('people.urls', namespace='people'), name='people'),
    path('missing/', include('missing.urls', namespace='missing'), name='missing'),
    path('permission/', include('permission.urls', namespace='permission'), name='permission'),
]