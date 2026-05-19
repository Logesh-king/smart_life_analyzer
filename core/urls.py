from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('daily-entry/', views.daily_entry_view, name='daily_entry'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('suggestions/', views.suggestions_view, name='suggestions'),
    path('settings/', views.settings_view, name='settings'),
]
