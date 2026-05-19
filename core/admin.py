from django.contrib import admin
from .models import UserProfile, DailyEntry, Suggestion


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'date_of_birth', 'gender', 'location', 'profile_photo', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_filter = ('gender', 'theme')


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'sleep_hours', 'work_hours', 'expense', 'mood', 'created_at')
    list_filter = ('mood', 'date', 'user')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'date'


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'severity', 'is_active', 'created_at')
    list_filter = ('severity', 'category', 'is_active')
    search_fields = ('title', 'description')
