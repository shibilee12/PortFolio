# movies/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('details/<int:movie_id>/', views.movie_details, name='movie_details'),
    path('base/', views.base, name='base'),
    path('homepage/', views.homepage, name='homepage'),
    path('settings/', views.settings, name='settings'),
]
