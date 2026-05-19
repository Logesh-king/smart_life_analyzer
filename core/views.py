import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Sum, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import LoginForm, SignupForm, DailyEntryForm, UserProfileForm, ProfilePhotoForm, PasswordChangeForm, ThemeForm
from .models import DailyEntry, UserProfile, Suggestion


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('home')

    login_form = LoginForm()
    signup_form = SignupForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'login':
            login_form = LoginForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                return redirect('home')
        elif action == 'signup':
            signup_form = SignupForm(request.POST)
            if signup_form.is_valid():
                user = signup_form.save()
                login(request, user)
                _generate_initial_suggestions(user)
                return redirect('home')

    return render(request, 'core/login.html', {
        'login_form': login_form,
        'signup_form': signup_form,
    })


def logout_view(request):
    """Handle user logout."""
    logout(request)
    return redirect('login')


@login_required
def home_view(request):
    """Dashboard overview / home page."""
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Get weekly stats
    weekly_entries = DailyEntry.objects.filter(user=user, date__gte=week_ago, date__lte=today)
    weekly_stats = weekly_entries.aggregate(
        avg_sleep=Avg('sleep_hours'),
        avg_work=Avg('work_hours'),
        avg_expense=Avg('expense'),
        total_work=Sum('work_hours'),
        total_expense=Sum('expense'),
    )

    # Today's entry
    today_entry = DailyEntry.objects.filter(user=user, date=today).first()

    # Latest suggestions (top 3)
    suggestions = Suggestion.objects.filter(user=user, is_active=True)[:3]

    # Weekly chart data
    chart_data = _get_weekly_chart_data(user, today)

    context = {
        'page': 'home',
        'avg_sleep': round(float(weekly_stats['avg_sleep'] or 0), 1),
        'avg_work': round(float(weekly_stats['avg_work'] or 0), 1),
        'avg_expense': round(float(weekly_stats['avg_expense'] or 0), 2),
        'total_work': round(float(weekly_stats['total_work'] or 0), 1),
        'total_expense': round(float(weekly_stats['total_expense'] or 0), 2),
        'today_entry': today_entry,
        'suggestions': suggestions,
        'chart_labels': json.dumps(chart_data['labels']),
        'chart_sleep': json.dumps(chart_data['sleep']),
        'chart_work': json.dumps(chart_data['work']),
        'productivity_score': _calc_productivity_score(weekly_entries),
        'expense_trend': _calc_expense_trend(user, today),
        'mood_trend': _get_mood_trend(weekly_entries),
    }
    return render(request, 'core/home.html', context)


@login_required
def daily_entry_view(request):
    """Daily entry form and recent entries."""
    user = request.user
    today = timezone.now().date()

    if request.method == 'POST':
        form = DailyEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = user
            # Update or create for this date
            existing = DailyEntry.objects.filter(user=user, date=entry.date).first()
            if existing:
                for field in ['sleep_hours', 'work_hours', 'expense', 'mood', 'notes']:
                    setattr(existing, field, getattr(entry, field))
                existing.save()
            else:
                entry.save()

            # Regenerate suggestions based on new data
            _auto_generate_suggestions(user)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Entry saved successfully!'})
            return redirect('daily_entry')

    form = DailyEntryForm(initial={'date': today})
    recent_entries = DailyEntry.objects.filter(user=user).order_by('-date')[:10]

    return render(request, 'core/daily_entry.html', {
        'page': 'daily-entry',
        'form': form,
        'recent_entries': recent_entries,
        'today': today.isoformat(),
    })


@login_required
def dashboard_view(request):
    """Analytics dashboard with charts and insights."""
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    weekly_entries = DailyEntry.objects.filter(user=user, date__gte=week_ago, date__lte=today)

    # Today's entry
    today_entry = DailyEntry.objects.filter(user=user, date=today).first()

    # Weekly aggregates
    weekly_stats = weekly_entries.aggregate(
        avg_sleep=Avg('sleep_hours'),
        total_work=Sum('work_hours'),
        total_expense=Sum('expense'),
        avg_expense=Avg('expense'),
    )

    # Mood chart data
    mood_data = _get_mood_chart_data(user, today)

    # Find highest spending day
    highest_day = weekly_entries.order_by('-expense').first()
    highest_spending_day = highest_day.date.strftime('%A') if highest_day else 'N/A'

    # Budget alerts count (days where expense > average * 1.3)
    avg_exp = weekly_stats['avg_expense'] or Decimal('0')
    budget_alerts = weekly_entries.filter(expense__gt=avg_exp * Decimal('1.3')).count() if avg_exp > 0 else 0

    context = {
        'page': 'dashboard',
        'today_entry': today_entry,
        'avg_sleep': round(float(weekly_stats['avg_sleep'] or 0), 1),
        'total_work': round(float(weekly_stats['total_work'] or 0), 1),
        'total_expense': round(float(weekly_stats['total_expense'] or 0), 2),
        'avg_expense': round(float(weekly_stats['avg_expense'] or 0), 2),
        'highest_spending_day': highest_spending_day,
        'budget_alerts': budget_alerts,
        'mood_labels': json.dumps(mood_data['labels']),
        'mood_scores': json.dumps(mood_data['scores']),
        'mood_colors': json.dumps(mood_data['colors']),
        'mood_borders': json.dumps(mood_data['borders']),
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def suggestions_view(request):
    """Smart suggestions page."""
    user = request.user

    # Auto-generate suggestions if none exist
    suggestions = Suggestion.objects.filter(user=user, is_active=True)
    if not suggestions.exists():
        _auto_generate_suggestions(user)
        suggestions = Suggestion.objects.filter(user=user, is_active=True)

    return render(request, 'core/suggestions.html', {
        'page': 'suggestions',
        'suggestions': suggestions,
    })


@login_required
def settings_view(request):
    """Account settings page with accordion sections."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    profile_form = UserProfileForm(instance=profile, user=user)
    photo_form = ProfilePhotoForm(instance=profile)
    theme_form = ThemeForm(instance=profile)
    password_form = PasswordChangeForm()
    success_message = None
    error_message = None
    active_section = None  # Which accordion to keep open after POST

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            active_section = 'personal-info'
            profile_form = UserProfileForm(request.POST, instance=profile, user=user)
            if profile_form.is_valid():
                profile = profile_form.save()
                user.username = profile_form.cleaned_data['username']
                user.first_name = profile_form.cleaned_data['first_name']
                user.last_name = profile_form.cleaned_data['last_name']
                user.email = profile_form.cleaned_data['email']
                user.save()
                success_message = 'Personal information updated successfully!'

        elif action == 'upload_photo':
            active_section = 'personal-info'
            photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)
            if photo_form.is_valid():
                photo_form.save()
                success_message = 'Profile photo updated successfully!'
            else:
                error_message = 'Failed to upload photo. Please try again with a valid image.'

        elif action == 'remove_photo':
            active_section = 'personal-info'
            if profile.profile_photo:
                profile.profile_photo.delete(save=True)
                success_message = 'Profile photo removed.'

        elif action == 'change_theme':
            active_section = 'themes'
            theme_form = ThemeForm(request.POST, instance=profile)
            if theme_form.is_valid():
                theme_form.save()
                success_message = f'Theme changed to {profile.get_theme_display()}!'

        elif action == 'change_password':
            active_section = 'change-password'
            password_form = PasswordChangeForm(request.POST)
            if password_form.is_valid():
                if user.check_password(password_form.cleaned_data['current_password']):
                    user.set_password(password_form.cleaned_data['new_password'])
                    user.save()
                    update_session_auth_hash(request, user)
                    success_message = 'Password changed successfully!'
                else:
                    error_message = 'Current password is incorrect.'

        elif action == 'export_data':
            active_section = 'account-management'
            # Build JSON export of user data
            import json as json_module
            from django.http import HttpResponse
            entries = list(DailyEntry.objects.filter(user=user).values(
                'date', 'sleep_hours', 'work_hours', 'expense', 'mood', 'notes'
            ))
            # Convert Decimal/date fields to strings
            for e in entries:
                e['date'] = str(e['date'])
                e['sleep_hours'] = float(e['sleep_hours'])
                e['work_hours'] = float(e['work_hours'])
                e['expense'] = float(e['expense'])
            export = {
                'user': {
                    'name': user.get_full_name(),
                    'email': user.email,
                    'phone': profile.phone,
                    'theme': profile.theme,
                },
                'entries': entries,
            }
            response = HttpResponse(
                json_module.dumps(export, indent=2),
                content_type='application/json'
            )
            response['Content-Disposition'] = 'attachment; filename="life_analyzer_export.json"'
            return response

        elif action == 'deactivate_account':
            active_section = 'account-management'
            user.is_active = False
            user.save()
            logout(request)
            return redirect('login')

    return render(request, 'core/settings.html', {
        'page': 'settings',
        'profile_form': profile_form,
        'photo_form': photo_form,
        'theme_form': theme_form,
        'password_form': password_form,
        'success_message': success_message,
        'error_message': error_message,
        'active_section': active_section,
        'current_theme': profile.theme,
    })


# ── Helper Functions ──────────────────────────────────────────────────

def _get_weekly_chart_data(user, today):
    """Build chart data for the weekly summary chart."""
    labels = []
    sleep_data = []
    work_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))
        entry = DailyEntry.objects.filter(user=user, date=day).first()
        sleep_data.append(float(entry.sleep_hours) if entry else 0)
        work_data.append(float(entry.work_hours) if entry else 0)
    return {'labels': labels, 'sleep': sleep_data, 'work': work_data}


def _get_mood_chart_data(user, today):
    """Build chart data for the mood tracker."""
    MOOD_COLORS = {
        'happy': ('rgba(76, 201, 240, 0.7)', '#4cc9f0'),
        'energetic': ('rgba(76, 201, 240, 0.7)', '#4cc9f0'),
        'neutral': ('rgba(67, 97, 238, 0.7)', '#4361ee'),
        'sad': ('rgba(247, 37, 133, 0.7)', '#f72585'),
        'stressed': ('rgba(248, 150, 30, 0.7)', '#f8961e'),
    }
    labels = []
    scores = []
    colors = []
    borders = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))
        entry = DailyEntry.objects.filter(user=user, date=day).first()
        if entry:
            scores.append(entry.get_mood_score())
            bg, border = MOOD_COLORS.get(entry.mood, ('rgba(67, 97, 238, 0.7)', '#4361ee'))
            colors.append(bg)
            borders.append(border)
        else:
            scores.append(0)
            colors.append('rgba(200, 200, 200, 0.3)')
            borders.append('#ccc')
    return {'labels': labels, 'scores': scores, 'colors': colors, 'borders': borders}


def _calc_productivity_score(entries):
    """Calculate productivity score from work hours."""
    if not entries.exists():
        return 0
    avg_work = float(entries.aggregate(avg=Avg('work_hours'))['avg'] or 0)
    return min(100, int((avg_work / 8.0) * 100))


def _calc_expense_trend(user, today):
    """Calculate expense trend vs previous week."""
    week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)

    this_week = DailyEntry.objects.filter(
        user=user, date__gte=week_ago, date__lte=today
    ).aggregate(total=Sum('expense'))['total'] or 0

    last_week = DailyEntry.objects.filter(
        user=user, date__gte=two_weeks_ago, date__lt=week_ago
    ).aggregate(total=Sum('expense'))['total'] or 0

    if last_week > 0:
        change = ((float(this_week) - float(last_week)) / float(last_week)) * 100
        return round(change)
    return 0


def _get_mood_trend(entries):
    """Determine the overall mood trend."""
    if not entries.exists():
        return 'neutral'
    moods = list(entries.values_list('mood', flat=True))
    positive = sum(1 for m in moods if m in ('happy', 'energetic'))
    negative = sum(1 for m in moods if m in ('sad', 'stressed'))
    if positive > negative:
        return 'positive'
    elif negative > positive:
        return 'negative'
    return 'stable'


def _generate_initial_suggestions(user):
    """Generate default suggestions for new users."""
    defaults = [
        {
            'title': 'Sleep Consistency',
            'description': 'Start tracking your sleep regularly. Maintaining a consistent bedtime between 10:30 PM - 11:00 PM is recommended for optimal rest.',
            'category': 'sleep',
            'severity': 'good',
        },
        {
            'title': 'Productivity Hours',
            'description': 'Track your most productive hours and schedule important tasks during those times for maximum efficiency.',
            'category': 'productivity',
            'severity': 'warning',
        },
        {
            'title': 'Expense Tracking',
            'description': 'Start logging your daily expenses to identify spending patterns and find areas to save.',
            'category': 'expense',
            'severity': 'warning',
        },
        {
            'title': 'Physical Activity',
            'description': 'Adding a 20-minute walk after lunch could improve your afternoon productivity by up to 15%.',
            'category': 'fitness',
            'severity': 'good',
        },
        {
            'title': 'Mental Wellness',
            'description': 'Consider adding mindfulness sessions to your routine to help manage stress levels.',
            'category': 'mental',
            'severity': 'good',
        },
        {
            'title': 'Weekly Review',
            'description': 'Set aside time each week to review your progress. Consistency is key to improvement!',
            'category': 'general',
            'severity': 'good',
        },
    ]
    for s in defaults:
        Suggestion.objects.create(user=user, **s)


def _auto_generate_suggestions(user):
    """Auto-generate suggestions based on user's data patterns."""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    entries = DailyEntry.objects.filter(user=user, date__gte=week_ago, date__lte=today)

    if entries.count() < 2:
        return

    # Deactivate old suggestions
    Suggestion.objects.filter(user=user).update(is_active=False)

    stats = entries.aggregate(
        avg_sleep=Avg('sleep_hours'),
        avg_work=Avg('work_hours'),
        avg_expense=Avg('expense'),
    )

    avg_sleep = float(stats['avg_sleep'] or 0)
    avg_work = float(stats['avg_work'] or 0)
    avg_expense = float(stats['avg_expense'] or 0)

    new_suggestions = []

    # Sleep suggestions
    if avg_sleep >= 7:
        new_suggestions.append({
            'title': 'Sleep Pattern Excellent',
            'description': f'Your average sleep of {avg_sleep:.1f} hours is great! Keep maintaining a regular bedtime schedule.',
            'category': 'sleep',
            'severity': 'good',
        })
    elif avg_sleep >= 6:
        new_suggestions.append({
            'title': 'Improve Sleep Duration',
            'description': f'Your average sleep of {avg_sleep:.1f} hours could be better. Aim for 7-8 hours per night.',
            'category': 'sleep',
            'severity': 'warning',
        })
    else:
        new_suggestions.append({
            'title': 'Critical: Sleep Deficit',
            'description': f'Your average sleep of {avg_sleep:.1f} hours is concerning. Lack of sleep severely impacts health and productivity.',
            'category': 'sleep',
            'severity': 'critical',
        })

    # Work/study suggestions
    if avg_work >= 7:
        new_suggestions.append({
            'title': 'Strong Work Ethic',
            'description': f'Averaging {avg_work:.1f} hours of work daily. Make sure to balance with rest and recreation.',
            'category': 'productivity',
            'severity': 'good',
        })
    elif avg_work >= 5:
        new_suggestions.append({
            'title': 'Study Hours Could Improve',
            'description': f'Your average of {avg_work:.1f} work hours has room for growth. Try focused time slots for deep work.',
            'category': 'productivity',
            'severity': 'warning',
        })
    else:
        new_suggestions.append({
            'title': 'Low Productivity Alert',
            'description': f'Averaging only {avg_work:.1f} hours of work. Consider creating a structured daily schedule.',
            'category': 'productivity',
            'severity': 'critical',
        })

    # Expense suggestions
    expense_trend = _calc_expense_trend(user, today)
    if expense_trend > 20:
        new_suggestions.append({
            'title': 'High Spending Alert',
            'description': f'Your expenses are {expense_trend}% above last week\'s average. Consider meal planning and budgeting.',
            'category': 'expense',
            'severity': 'critical',
        })
    elif expense_trend > 0:
        new_suggestions.append({
            'title': 'Spending Slightly Increased',
            'description': f'Expenses up {expense_trend}% from last week. Keep an eye on discretionary spending.',
            'category': 'expense',
            'severity': 'warning',
        })
    else:
        new_suggestions.append({
            'title': 'Good Spending Habits',
            'description': f'Your expenses are well controlled. Average daily spend: ${avg_expense:.2f}.',
            'category': 'expense',
            'severity': 'good',
        })

    # Mood suggestions
    moods = list(entries.values_list('mood', flat=True))
    stressed_count = moods.count('stressed') + moods.count('sad')
    if stressed_count >= 3:
        new_suggestions.append({
            'title': 'Mental Wellness Alert',
            'description': 'You\'ve reported stress or sadness frequently this week. Consider scheduling lighter workloads or adding mindfulness sessions.',
            'category': 'mental',
            'severity': 'critical',
        })
    else:
        new_suggestions.append({
            'title': 'Physical Activity',
            'description': 'Adding a 20-minute walk after lunch could improve your afternoon productivity by 15%.',
            'category': 'fitness',
            'severity': 'good',
        })

    # General weekly review
    new_suggestions.append({
        'title': 'Weekly Review',
        'description': f'You\'ve logged {entries.count()} entries this week. Keep tracking consistently for better insights!',
        'category': 'general',
        'severity': 'good',
    })

    for s in new_suggestions:
        Suggestion.objects.create(user=user, **s)
