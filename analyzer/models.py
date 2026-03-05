from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, Avg, Count, Q
from datetime import date, timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    email_notifications = models.BooleanField(default=True)
    daily_reminders = models.BooleanField(default=True)
    weekly_reports = models.BooleanField(default=True)
    reminder_time = models.TimeField(default='20:00:00')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username
    
    @property
    def initials(self):
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        return self.user.username[0].upper()
    
    class Meta:
        ordering = ['-created_at']

class DailyEntry(models.Model):
    class Mood(models.TextChoices):
        HAPPY = 'happy', '😊 Happy'
        NEUTRAL = 'neutral', '😐 Neutral'
        SAD = 'sad', '😔 Sad'
        STRESSED = 'stressed', '😫 Stressed'
        ENERGETIC = 'energetic', '😎 Energetic'
        TIRED = 'tired', '😴 Tired'
        ANGRY = 'angry', '😠 Angry'
        SICK = 'sick', '🤒 Sick'

    MOOD_SCORES = {
        Mood.HAPPY: 9,
        Mood.ENERGETIC: 8,
        Mood.NEUTRAL: 5,
        Mood.TIRED: 4,
        Mood.STRESSED: 3,
        Mood.SAD: 2,
        Mood.SICK: 2,
        Mood.ANGRY: 1,
    }

    MOOD_EMOJIS = {
        Mood.HAPPY: '😊',
        Mood.NEUTRAL: '😐',
        Mood.SAD: '😔',
        Mood.STRESSED: '😫',
        Mood.ENERGETIC: '😎',
        Mood.TIRED: '😴',
        Mood.ANGRY: '😠',
        Mood.SICK: '🤒',
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    date = models.DateField(default=timezone.now)
    sleep_hours = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    work_hours = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    exercise_minutes = models.PositiveIntegerField(default=0, null=True, blank=True)
    water_intake = models.PositiveIntegerField(default=0, null=True, blank=True)
    expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    income = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    mood = models.CharField(max_length=20, choices=Mood.choices, default=Mood.NEUTRAL)
    stress_level = models.PositiveIntegerField(default=0, null=True, blank=True)
    energy_level = models.PositiveIntegerField(default=0, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    @property
    def mood_score(self):
        return self.MOOD_SCORES.get(self.mood, 5)
    
    @property
    def mood_emoji(self):
        return self.MOOD_EMOJIS.get(self.mood, '😐')

class Suggestion(models.Model):
    class Category(models.TextChoices):
        SLEEP = 'sleep', 'Sleep'
        WORK = 'work', 'Work/Study'
        FINANCE = 'finance', 'Finance'
        HEALTH = 'health', 'Health'
        MOOD = 'mood', 'Mood'
        EXERCISE = 'exercise', 'Exercise'
        GENERAL = 'general', 'General'

    class Priority(models.TextChoices):
        GOOD = 'good', 'Good'
        WARNING = 'warning', 'Warning'
        CRITICAL = 'critical', 'Critical'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suggestions')
    category = models.CharField(max_length=20, choices=Category.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"

class Analytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    period = models.CharField(max_length=20)
    period_start = models.DateField()
    period_end = models.DateField()
    avg_sleep = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_work = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    total_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mood_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'period', 'period_start']
    
    def __str__(self):
        return f"{self.user.username} - {self.period} - {self.period_start}"

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50)
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"