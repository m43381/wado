# department/urls.py

from django.urls import path, include
from . import views

app_name = 'department'

urlpatterns = [
    path('profile/', views.DepartmentDashboardView.as_view(), name='profile'),
    path('people/', include('people.urls', namespace='people')),
    path('missing/', include('missing.urls', namespace='missing')),
    path('permission/', include('permission.urls', namespace='permission')),
    path('duty/', include(('duty.urls_department', 'department_duty'), namespace='duty')),
]