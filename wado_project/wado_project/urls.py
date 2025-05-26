from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('notifications/', include('notifications.urls')),
    path('authentication/', include('authentication.urls')),
    path('department/', include('department.urls')),
    path('commandant/', include('commandant.urls')),
    path('faculty/', include('faculty.urls')),
    path('', views.homepage, name='home'),
]