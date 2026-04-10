from django.urls import path
from . import views

urlpatterns = [
    path('dashboard', views.weather_dashboard, name='home'),
    path('', views.weather_dashboard, name='weather_dashboard'),
]
