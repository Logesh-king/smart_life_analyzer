from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import json
from .models import DailyEntry, UserProfile, Suggestion, Goal
from .forms import LoginForm, SignupForm, DailyEntryForm, UserProfileForm, UserUpdateForm, PasswordChangeForm
from .utils import generate_suggestions, calculate_stats, calculate_analytics

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'analyzer/login.html', {'form': form})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create sample suggestions
            Suggestion.objects.create(
                user=user,
                category=Suggestion.Category.GENERAL,
                priority=Suggestion.Priority.GOOD,
                title='Welcome to Smart Life Analyzer!',
                description='Start by adding your daily entries to track your sleep, work, expenses, and mood. The more data you add, the better suggestions you\'ll receive.'
            )
            
            # Specify backend to ensure login API compatibility
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = SignupForm()
    
    return render(request, 'analyzer/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def home_view(request):
    today = timezone.now().date()
    
    # Get today's entry
    today_entry = DailyEntry.objects.filter(user=request.user, date=today).first()
    
    # Calculate last 7 days stats
    start_date = today - timedelta(days=7)
    entries = DailyEntry.objects.filter(user=request.user, date__range=[start_date, today]).order_by('date')
    
    # Use centralized stats
    stats = calculate_stats(entries)
    
    # Get recent entries for chart
    dates = [entry.date.strftime('%a') for entry in entries]
    sleep_data = [float(entry.sleep_hours) for entry in entries]
    work_data = [float(entry.work_hours) for entry in entries]
    
    # Get suggestions
    suggestions = Suggestion.objects.filter(user=request.user, is_active=True).order_by('-created_at')[:3]
    
    # Calculate productivity score
    avg_work = stats['total_work'] / 7  # Approximate daily average over the week window
    if avg_work > 0:
        productivity_score = min(100, int((avg_work / 8) * 100))
    else:
        productivity_score = 0
    
    context = {
        'today_entry': today_entry,
        'avg_sleep': stats['avg_sleep'],
        'avg_work': round(avg_work, 1),
        'avg_expense': round(stats['total_expense'] / 7, 2), # Approximate daily average
        'productivity_score': productivity_score,
        'suggestions': suggestions,
        'dates_json': json.dumps(dates),
        'sleep_data_json': json.dumps(sleep_data),
        'work_data_json': json.dumps(work_data),
    }
    
    return render(request, 'analyzer/home.html', context)

@login_required
def daily_entry_view(request):
    today = timezone.now().date()
    
    if request.method == 'POST':
        form = DailyEntryForm(request.POST)
        # Handle the case where the form is bound to an existing instance if one exists for the date.
        # But here the logic separates creation and update.
        # Let's verify if we are posting to update or create
        submitted_date = request.POST.get('date')
        
        # If the form instance is not set, we need to check if an entry exists for the submitted date (or today if not in post)
        # Ideally, the form should handle validation, but to support the overwrite logic:
        
        # Simpler logic:
        # Check if entry exists for this date
        date_val = submitted_date if submitted_date else today
        existing_entry = DailyEntry.objects.filter(user=request.user, date=date_val).first()
        
        if existing_entry:
            form = DailyEntryForm(request.POST, instance=existing_entry)
        
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            
            msg = 'Entry updated successfully!' if existing_entry else 'Daily entry saved successfully!'
            messages.success(request, msg)
            
            # Generate new suggestions
            generate_suggestions(request.user)
            
            return redirect('daily_entry')
    else:
        # Try to get today's entry
        entry = DailyEntry.objects.filter(user=request.user, date=today).first()
        form = DailyEntryForm(instance=entry, initial={'date': today})
    
    # Get recent entries
    recent_entries = DailyEntry.objects.filter(user=request.user).order_by('-date')[:5]
    
    # Mood choices for template
    mood_choices = [
        (mood.value, mood.label, DailyEntry.MOOD_EMOJIS[mood])
        for mood in DailyEntry.Mood
    ]
    
    context = {
        'form': form,
        'today': today,
        'recent_entries': recent_entries,
        'mood_choices': mood_choices,
    }
    
    return render(request, 'analyzer/daily_entry.html', context)

@login_required
def dashboard_view(request):
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    # Get entries for last 30 days
    entries = DailyEntry.objects.filter(user=request.user, date__range=[start_date, today]).order_by('date')
    
    # Prepare data for charts
    dates = [entry.date.strftime('%Y-%m-%d') for entry in entries]
    sleep_data = [float(entry.sleep_hours) for entry in entries]
    work_data = [float(entry.work_hours) for entry in entries]
    expense_data = [float(entry.expense) for entry in entries]
    
    # Calculate statistics
    stats = calculate_stats(entries)
    
    # Calculate weekly stats
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    weekly_entries = entries.filter(date__range=[week_start, week_end])
    weekly_stats = calculate_stats(weekly_entries)
    
    # Calculate expense insights
    expense_insights = calculate_expense_insights(request.user)
    
    context = {
        'dates_json': json.dumps(dates),
        'sleep_data_json': json.dumps(sleep_data),
        'work_data_json': json.dumps(work_data),
        'expense_data_json': json.dumps(expense_data),
        'avg_sleep': stats['avg_sleep'],
        'total_work': stats['total_work'],
        'total_expense': stats['total_expense'],
        'mood_counts': stats['mood_distribution'],
        'weekly_avg_sleep': weekly_stats['avg_sleep'],
        'weekly_total_work': weekly_stats['total_work'],
        'weekly_total_expense': weekly_stats['total_expense'],
        'week_start': week_start,
        'week_end': week_end,
        'expense_insights': expense_insights,
        'today': today,
    }
    
    return render(request, 'analyzer/dashboard.html', context)

@login_required
def suggestions_view(request):
    # Generate suggestions if needed
    generate_suggestions(request.user)
    
    # Get all active suggestions
    suggestions = Suggestion.objects.filter(user=request.user, is_active=True).order_by('-created_at')
    
    # Group by priority
    good_suggestions = suggestions.filter(priority='good')
    warning_suggestions = suggestions.filter(priority='warning')
    critical_suggestions = suggestions.filter(priority='critical')
    
    context = {
        'good_suggestions': good_suggestions,
        'warning_suggestions': warning_suggestions,
        'critical_suggestions': critical_suggestions,
        'total_suggestions': suggestions.count(),
    }
    
    return render(request, 'analyzer/suggestions.html', context)

@login_required
def settings_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=user)
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('settings')
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.POST)
            if password_form.is_valid():
                current_password = password_form.cleaned_data['current_password']
                new_password = password_form.cleaned_data['new_password']
                confirm_password = password_form.cleaned_data['confirm_password']
                
                if user.check_password(current_password):
                    if new_password == confirm_password:
                        user.set_password(new_password)
                        user.save()
                        update_session_auth_hash(request, user)
                        messages.success(request, 'Password changed successfully!')
                        return redirect('settings')
                    else:
                        messages.error(request, 'New passwords do not match.')
                else:
                    messages.error(request, 'Current password is incorrect.')
    
    user_form = UserUpdateForm(instance=user)
    profile_form = UserProfileForm(instance=profile)
    password_form = PasswordChangeForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
        'profile': profile,
    }
    
    return render(request, 'analyzer/settings.html', context)

# Helper functions
def calculate_expense_insights(user):
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    entries = DailyEntry.objects.filter(
        user=user,
        date__range=[start_date, today]
    )
    
    if not entries.exists():
        return {
            'avg_daily': 0,
            'highest_day': {'day': 'N/A', 'amount': 0},
            'alerts_count': 0,
        }
    
    stats = calculate_stats(entries)
    # Re-calculate average daily from DB or aggregate, since calculate_stats might not give exactly what we need for this specific view if it's strictly Sum
    # Actually calculate_stats returns 'total_expense'.
    # For daily average we can just divide total by days count or re-aggregate
    
    avg_daily = entries.aggregate(Avg('expense'))['expense__avg'] or 0
    
    # Find highest spending day
    highest_entry = entries.order_by('-expense').first()
    highest_day = {
        'day': highest_entry.date.strftime('%A'),
        'amount': float(highest_entry.expense)
    }
    
    # Count days with high expenses (over $50)
    alerts_count = entries.filter(expense__gt=50).count()
    
    return {
        'avg_daily': round(avg_daily, 2),
        'highest_day': highest_day,
        'alerts_count': alerts_count,
    }