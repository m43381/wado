# authentication/urls.py
from authentication.views import ProfileRedirectView
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', ProfileRedirectView.as_view(), name='profile_redirect'),
]