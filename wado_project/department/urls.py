from django.urls import path, include
from . import views

app_name = 'department'

urlpatterns = [
    path('profile/', views.DepartmentDashboardView.as_view(), name='profile'),
    path('people/', include('people.urls', namespace='people'), name='people')
]