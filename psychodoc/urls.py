from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='psychodoc_dashboard'),
    path('journal/', views.journal, name='psychodoc_journal'),
    path('signup/', views.signup, name='psychodoc_signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='psychodoc_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='psychodoc_login'), name='psychodoc_logout'),
    path('mood-data/', views.mood_data, name='psychodoc_mood_data'),
    path('ai-chat/',views.ai_chat, name='psychodoc_ai_chat'),
    path('analyze-journal/',views.analyze_journal_with_ai, name='psychodoc_analyze_journal'),
    path('reflect-with-ai/', views.reflect_with_ai, name='psychodoc_reflect_ai'),

]

