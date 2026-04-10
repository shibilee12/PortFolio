from django.urls import path
from . import views

urlpatterns = [
    path('', views.board, name='musixboard_board'),
]