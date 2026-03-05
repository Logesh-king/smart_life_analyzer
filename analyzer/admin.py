from django.contrib import admin
from .models import UserProfile, DailyEntry, Suggestion, Analytics

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'age']
    search_fields = ['user__username', 'phone']

@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'sleep_hours', 'work_hours', 'expense', 'mood']
    list_filter = ['date', 'mood']
    search_fields = ['user', 'notes']
    date_hierarchy = 'date'

@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'priority', 'title', 'is_active']
    list_filter = ['category', 'priority', 'is_active']
    search_fields = ['title', 'description']

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'period', 'period_start', 'avg_sleep']
    list_filter = ['period', 'period_start']
# Register your models here.
