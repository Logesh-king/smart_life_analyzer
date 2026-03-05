from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import api_views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='analyzer/password_reset/password_reset.html',
             email_template_name='analyzer/password_reset/password_reset_email.html',
             subject_template_name='analyzer/password_reset/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='analyzer/password_reset/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='analyzer/password_reset/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='analyzer/password_reset/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Main pages
    path('home/', views.home_view, name='home'),
    path('daily-entry/', views.daily_entry_view, name='daily_entry'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('suggestions/', views.suggestions_view, name='suggestions'),
    path('settings/', views.settings_view, name='settings'),
    
    # API endpoints
    path('api/', api_views.api_base, name='api_base'),
    path('api/weekly-summary/', api_views.api_weekly_summary, name='api_weekly_summary'),
    path('api/daily-entry/', api_views.api_daily_entry, name='api_daily_entry'),
    path('api/daily-entry/<int:entry_id>/', api_views.api_daily_entry, name='api_daily_entry_detail'),
    path('api/recent-entries/', api_views.api_recent_entries, name='api_recent_entries'),
    path('api/mood-data/', api_views.api_mood_data, name='api_mood_data'),
    path('api/expense-data/', api_views.api_expense_data, name='api_expense_data'),
    path('api/ai-suggestions/', api_views.api_ai_suggestions, name='api_ai_suggestions'),
    path('api/suggestions/', api_views.api_suggestions, name='api_suggestions'),
    path('api/suggestion/<int:suggestion_id>/read/', api_views.api_mark_suggestion_read, name='api_mark_suggestion_read'),
    path('api/suggestion/<int:suggestion_id>/dismiss/', api_views.api_dismiss_suggestion, name='api_dismiss_suggestion'),
    path('api/update-profile/', api_views.api_update_profile, name='api_update_profile'),
    path('api/change-password/', api_views.api_change_password, name='api_change_password'),
    path('api/save-preferences/', api_views.api_save_preferences, name='api_save_preferences'),
    path('api/export-data/', api_views.api_export_data, name='api_export_data'),
    path('api/delete-account/', api_views.api_delete_account, name='api_delete_account'),
    path('api/today-stats/', api_views.api_today_stats, name='api_today_stats'),
    path('api/weekly-stats/', api_views.api_weekly_stats, name='api_weekly_stats'),
    path('api/expense-insights/', api_views.api_expense_insights, name='api_expense_insights'),
]