from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with additional personal information."""

    THEME_CHOICES = [
        ('default', 'Default Blue'),
        ('dark', 'Dark Mode'),
        ('ocean', 'Ocean Breeze'),
        ('sunset', 'Sunset Glow'),
        ('forest', 'Forest Green'),
        ('lavender', 'Lavender Dream'),
    ]

    GENDER_CHOICES = [
        ('', 'Prefer not to say'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, default='')
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='default')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"

    def get_initials(self):
        """Return user initials for the avatar."""
        first = self.user.first_name[:1].upper() if self.user.first_name else ''
        last = self.user.last_name[:1].upper() if self.user.last_name else ''
        return f"{first}{last}" or self.user.username[:2].upper()

    def get_photo_url(self):
        """Return the profile photo URL, or None if not set."""
        if self.profile_photo and hasattr(self.profile_photo, 'url'):
            return self.profile_photo.url
        return None


class DailyEntry(models.Model):
    """Daily life tracking entry."""
    MOOD_CHOICES = [
        ('happy', '😊 Happy'),
        ('neutral', '😐 Neutral'),
        ('sad', '😔 Sad'),
        ('stressed', '😫 Stressed'),
        ('energetic', '😎 Energetic'),
    ]

    MOOD_EMOJIS = {
        'happy': '😊',
        'neutral': '😐',
        'sad': '😔',
        'stressed': '😫',
        'energetic': '😎',
    }

    MOOD_SCORES = {
        'happy': 8,
        'energetic': 9,
        'neutral': 6,
        'sad': 3,
        'stressed': 4,
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_entries')
    date = models.DateField(default=timezone.now)
    sleep_hours = models.DecimalField(max_digits=4, decimal_places=1)
    work_hours = models.DecimalField(max_digits=4, decimal_places=1)
    expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='neutral')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']
        verbose_name_plural = 'Daily Entries'

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    def get_mood_emoji(self):
        return self.MOOD_EMOJIS.get(self.mood, '😐')

    def get_mood_score(self):
        return self.MOOD_SCORES.get(self.mood, 5)


class Suggestion(models.Model):
    """AI-powered lifestyle suggestions."""
    CATEGORY_CHOICES = [
        ('sleep', 'Sleep'),
        ('productivity', 'Productivity'),
        ('expense', 'Expense'),
        ('fitness', 'Fitness'),
        ('mental', 'Mental Wellness'),
        ('general', 'General'),
    ]

    SEVERITY_CHOICES = [
        ('good', 'Good'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    SEVERITY_ICONS = {
        'good': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'critical': 'fas fa-fire',
    }

    CATEGORY_ICONS = {
        'sleep': 'fas fa-bed',
        'productivity': 'fas fa-clock',
        'expense': 'fas fa-utensils',
        'fitness': 'fas fa-running',
        'mental': 'fas fa-brain',
        'general': 'fas fa-chart-line',
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suggestions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='good')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.severity})"

    def get_severity_icon(self):
        return self.SEVERITY_ICONS.get(self.severity, 'fas fa-info-circle')

    def get_category_icon(self):
        return self.CATEGORY_ICONS.get(self.category, 'fas fa-lightbulb')
