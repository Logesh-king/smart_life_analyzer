from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from django.shortcuts import get_object_or_404
from datetime import timedelta, datetime
import json
import csv
from .models import DailyEntry, UserProfile, Suggestion
from .forms import DailyEntryForm, UserUpdateForm, UserProfileForm, PasswordChangeForm
from .utils import calculate_stats, get_suggestion_data

# Base API endpoint
@login_required
def api_base(request):
    return JsonResponse({
        'success': True,
        'message': 'Smart Life Analyzer API',
        'version': '1.0',
        'user': request.user.username
    })

@login_required
@require_http_methods(["GET"])
def api_weekly_summary(request):
    """API endpoint for weekly summary data"""
    today = timezone.now().date()
    start_date = today - timedelta(days=7)
    
    entries = DailyEntry.objects.filter(
        user=request.user,
        date__range=[start_date, today]
    ).order_by('date')
    
    # Create a map of date -> entry for O(1) lookup
    entries_map = {entry.date: entry for entry in entries}
    
    # Get all dates in the range
    all_dates = [start_date + timedelta(days=i) for i in range(8)]
    
    sleep_data = []
    work_data = []
    expense_data = []
    labels = []
    
    for date in all_dates:
        labels.append(date.strftime('%a'))
        entry = entries_map.get(date)
        if entry:
            sleep_data.append(float(entry.sleep_hours))
            work_data.append(float(entry.work_hours))
            expense_data.append(float(entry.expense))
        else:
            sleep_data.append(0)
            work_data.append(0)
            expense_data.append(0)
    
    data = {
        'success': True,
        'data': {
            'labels': labels,
            'sleep_data': sleep_data,
            'work_data': work_data,
            'expense_data': expense_data,
        }
    }
    
    return JsonResponse(data)

@login_required
@csrf_exempt
@require_http_methods(["POST", "GET", "PUT", "DELETE"])
def api_daily_entry(request, entry_id=None):
    """API endpoint for daily entry CRUD operations"""
    if request.method == 'POST':
        return _handle_post_entry(request)
    
    elif request.method == 'GET' and entry_id:
        return _handle_get_entry(request, entry_id)
    
    elif request.method == 'PUT' and entry_id:
        return _handle_put_entry(request, entry_id)
    
    elif request.method == 'DELETE' and entry_id:
        return _handle_delete_entry(request, entry_id)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def _handle_post_entry(request):
    date = request.POST.get('date')
    if not date:
        return JsonResponse({'success': False, 'message': 'Date is required'}, status=400)
        
    instance = DailyEntry.objects.filter(user=request.user, date=date).first()
    form = DailyEntryForm(request.POST, instance=instance)
    
    if form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.save()
        message = 'Entry updated successfully' if instance else 'Entry saved successfully'
        return JsonResponse({'success': True, 'message': message, 'entry_id': entry.id})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid form data', 'errors': form.errors}, status=400)

def _handle_get_entry(request, entry_id):
    entry = get_object_or_404(DailyEntry, id=entry_id, user=request.user)
    return JsonResponse({
        'success': True,
        'entry': {
            'id': entry.id,
            'date': entry.date.strftime('%Y-%m-%d'),
            'sleep_hours': float(entry.sleep_hours),
            'work_hours': float(entry.work_hours),
            'expense': float(entry.expense),
            'mood': entry.mood,
            'notes': entry.notes
        }
    })

def _handle_put_entry(request, entry_id):
    entry = get_object_or_404(DailyEntry, id=entry_id, user=request.user)
    try:
        data = json.loads(request.body)
        form = DailyEntryForm(data, instance=entry)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Entry updated'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

def _handle_delete_entry(request, entry_id):
    entry = get_object_or_404(DailyEntry, id=entry_id, user=request.user)
    entry.delete()
    return JsonResponse({'success': True, 'message': 'Entry deleted'})

@login_required
@require_http_methods(["GET"])
def api_recent_entries(request):
    """API endpoint for recent entries"""
    entries = DailyEntry.objects.filter(user=request.user).order_by('-date')[:10]
    
    data = {
        'success': True,
        'entries': [
            {
                'id': entry.id,
                'date': entry.date.strftime('%Y-%m-%d'),
                'sleep_hours': float(entry.sleep_hours),
                'work_hours': float(entry.work_hours),
                'expense': float(entry.expense),
                'mood': entry.mood,
                'notes': entry.notes,
                'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M')
            }
            for entry in entries
        ]
    }
    
    return JsonResponse(data)

@login_required
@require_http_methods(["GET"])
def api_mood_data(request):
    """API endpoint for mood tracking data"""
    try:
        days = int(request.GET.get('days', 7))
    except ValueError:
        days = 7
        
    today = timezone.now().date()
    start_date = today - timedelta(days=days-1)
    
    entries = DailyEntry.objects.filter(
        user=request.user,
        date__range=[start_date, today]
    ).order_by('date')
    
    entries_map = {entry.date: entry for entry in entries}
    mood_scores = DailyEntry.MOOD_SCORES
    
    labels = []
    scores = []
    moods = []
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        labels.append(date.strftime('%b %d'))
        
        entry = entries_map.get(date)
        if entry:
            scores.append(mood_scores.get(entry.mood, 5))
            moods.append(entry.get_mood_display())
        else:
            scores.append(None)
            moods.append('No data')
    
    valid_scores = [s for s in scores if s is not None]
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    data = {
        'success': True,
        'data': {
            'labels': labels,
            'scores': scores,
            'moods': moods,
            'avg_score': avg_score
        }
    }
    
    return JsonResponse(data)

@login_required
@require_http_methods(["GET"])
def api_expense_data(request):
    """API endpoint for expense data"""
    today = timezone.now().date()
    start_date = today - timedelta(days=6)
    
    entries = DailyEntry.objects.filter(
        user=request.user,
        date__range=[start_date, today]
    ).order_by('date')
    
    entries_map = {entry.date: entry for entry in entries}
    
    labels = []
    amounts = []
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        labels.append(date.strftime('%a'))
        entry = entries_map.get(date)
        amounts.append(float(entry.expense) if entry else 0)
    
    data = {
        'success': True,
        'data': {
            'labels': labels,
            'amounts': amounts,
            'total': sum(amounts),
            'average': sum(amounts) / len(amounts) if amounts else 0
        }
    }
    
    return JsonResponse(data)

@login_required
@require_http_methods(["GET"])
def api_ai_suggestions(request):
    """API endpoint for AI-powered suggestions"""
    suggestions = get_suggestion_data(request.user)
    return JsonResponse({
        'success': True,
        'suggestions': suggestions[:6]
    })

@login_required
@require_http_methods(["GET"])
def api_suggestions(request):
    """API endpoint for user suggestions"""
    suggestions = Suggestion.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-created_at')
    
    data = {
        'success': True,
        'suggestions': [
            {
                'id': s.id,
                'title': s.title,
                'description': s.description,
                'category': s.category,
                'category_display': s.get_category_display(),
                'priority': s.priority,
                'created_at': s.created_at.strftime('%Y-%m-%d'),
                'is_read': s.is_read
            }
            for s in suggestions
        ]
    }
    
    return JsonResponse(data)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_mark_suggestion_read(request, suggestion_id):
    """Mark a suggestion as read"""
    suggestion = get_object_or_404(Suggestion, id=suggestion_id, user=request.user)
    suggestion.is_read = True
    suggestion.save()
    return JsonResponse({'success': True})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_dismiss_suggestion(request, suggestion_id):
    """Dismiss a suggestion"""
    suggestion = get_object_or_404(Suggestion, id=suggestion_id, user=request.user)
    suggestion.is_active = False
    suggestion.save()
    return JsonResponse({'success': True})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_update_profile(request):
    """API endpoint for updating user profile"""
    user_form = UserUpdateForm(request.POST, instance=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
    
    if user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }
        })
    
    errors = {}
    if user_form.errors: errors.update(user_form.errors)
    if profile_form.errors: errors.update(profile_form.errors)
    
    return JsonResponse({'success': False, 'message': 'Invalid form data', 'errors': errors}, status=400)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_change_password(request):
    """API endpoint for changing password"""
    form = PasswordChangeForm(request.POST)
    if form.is_valid():
        current_password = form.cleaned_data['current_password']
        new_password = form.cleaned_data['new_password']
        confirm_password = form.cleaned_data['confirm_password']
        
        if not request.user.check_password(current_password):
            return JsonResponse({'success': False, 'message': 'Current password is incorrect'}, status=400)
            
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'New passwords do not match'}, status=400)
            
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        return JsonResponse({'success': True, 'message': 'Password changed successfully'})
            
    return JsonResponse({'success': False, 'message': 'Invalid form data', 'errors': form.errors}, status=400)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_save_preferences(request):
    """API endpoint for saving user preferences"""
    try:
        data = json.loads(request.body)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.preferences = data
        profile.save()
        return JsonResponse({'success': True, 'message': 'Preferences saved successfully'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)

@login_required
@require_http_methods(["GET"])
def api_export_data(request):
    """API endpoint for exporting user data"""
    # Fetch all data efficiently
    entries = DailyEntry.objects.filter(user=request.user).order_by('-date')
    suggestions = Suggestion.objects.filter(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    export_data = {
        'user': {
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'date_joined': request.user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
        },
        'profile': {
            'phone': profile.phone,
            'age': profile.age,
            'date_of_birth': str(profile.date_of_birth) if profile.date_of_birth else None,
        },
        'entries': [
            {
                'date': str(entry.date),
                'sleep_hours': float(entry.sleep_hours),
                'work_hours': float(entry.work_hours),
                'expense': float(entry.expense),
                'mood': entry.mood,
                'notes': entry.notes,
                'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for entry in entries
        ],
        'suggestions': [
            {
                'title': s.title,
                'description': s.description,
                'category': s.category,
                'priority': s.priority,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': s.is_active,
                'is_read': s.is_read
            }
            for s in suggestions
        ],
        'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    response = JsonResponse(export_data)
    response['Content-Disposition'] = f'attachment; filename="smart_life_data_{request.user.username}_{datetime.now().strftime("%Y%m%d")}.json"'
    return response

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_delete_account(request):
    """API endpoint for deleting user account"""
    try:
        data = json.loads(request.body)
        if data.get('confirm') is True:
            request.user.delete()
            return JsonResponse({'success': True, 'message': 'Account deleted successfully'})
        return JsonResponse({'success': False, 'message': 'Confirmation required'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)

@login_required
@require_http_methods(["GET"])
def api_today_stats(request):
    """API endpoint for today's statistics"""
    today = timezone.now().date()
    entry = DailyEntry.objects.filter(user=request.user, date=today).first()
    
    if entry:
        stats = {
            'sleep': float(entry.sleep_hours),
            'work': float(entry.work_hours),
            'expense': float(entry.expense),
            'mood': entry.get_mood_display(),
            'mood_value': entry.mood,
            'has_entry': True
        }
    else:
        stats = {
            'sleep': 0, 'work': 0, 'expense': 0,
            'mood': 'No data', 'mood_value': 'neutral',
            'has_entry': False
        }
    
    return JsonResponse({
        'success': True,
        'stats': stats,
        'date': today.strftime('%Y-%m-%d')
    })

@login_required
@require_http_methods(["GET"])
def api_weekly_stats(request):
    """API endpoint for weekly statistics"""
    today = timezone.now().date()
    start_date = today - timedelta(days=6)
    
    entries = DailyEntry.objects.filter(
        user=request.user,
        date__range=[start_date, today]
    )
    
    current_stats = calculate_stats(entries)
    
    # Get previous week for comparison
    prev_start = start_date - timedelta(days=7)
    prev_end = start_date - timedelta(days=1)
    prev_entries = DailyEntry.objects.filter(
        user=request.user,
        date__range=[prev_start, prev_end]
    )
    prev_stats = calculate_stats(prev_entries)
    
    # Calculate trends
    def get_trend(current, previous):
        if previous > 0:
            change = ((current - previous) / previous) * 100
            trend = 'up' if change > 0 else 'down' if change < 0 else 'stable'
            return round(abs(change), 1), trend
        return 0, 'stable'
        
    sleep_change, sleep_trend = get_trend(current_stats['avg_sleep'], prev_stats['avg_sleep'])
    work_change, work_trend = get_trend(current_stats['total_work'], prev_stats['total_work'])
    expense_change, expense_trend = get_trend(current_stats['total_expense'], prev_stats['total_expense'])
    
    stats = {
        'avg_sleep': current_stats['avg_sleep'],
        'total_work': current_stats['total_work'],
        'total_expense': current_stats['total_expense'],
        'sleep_change': sleep_change,
        'work_change': work_change,
        'expense_change': expense_change,
        'sleep_trend': sleep_trend,
        'work_trend': work_trend,
        'expense_trend': expense_trend,
        'week_start': start_date.strftime('%Y-%m-%d'),
        'week_end': today.strftime('%Y-%m-%d')
    }
    
    return JsonResponse({'success': True, 'stats': stats})

@login_required
@require_http_methods(["GET"])
def api_expense_insights(request):
    """API endpoint for expense insights"""
    today = timezone.now().date()
    start_date = today - timedelta(days=6)
    
    entries = DailyEntry.objects.filter(
        user=request.user,
        date__range=[start_date, today]
    )
    
    if not entries.exists():
        return JsonResponse({
            'success': True,
            'insights': {
                'avg_daily': 0,
                'highest_day': {'day': 'N/A', 'amount': 0},
                'alerts_count': 0,
                'avg_by_day': {},
                'total_expenses': 0
            }
        })

    # Use calculate_stats for total expense
    stats = calculate_stats(entries)
    total_expenses = stats['total_expense']
    avg_daily = entries.aggregate(Avg('expense'))['expense__avg'] or 0
    
    highest_entry = entries.order_by('-expense').first()
    highest_day = {
        'day': highest_entry.date.strftime('%A'),
        'date': highest_entry.date.strftime('%Y-%m-%d'),
        'amount': float(highest_entry.expense)
    }
    
    alerts_count = entries.filter(expense__gt=50).count()
    
    # Calculate expense by day of week
    expense_by_day = {}
    for entry in entries:
        day_name = entry.date.strftime('%A')
        expense_by_day.setdefault(day_name, []).append(float(entry.expense))
    
    avg_by_day = {day: sum(amts)/len(amts) for day, amts in expense_by_day.items()}
    
    return JsonResponse({
        'success': True,
        'insights': {
            'avg_daily': round(avg_daily, 2),
            'highest_day': highest_day,
            'alerts_count': alerts_count,
            'avg_by_day': avg_by_day,
            'total_expenses': total_expenses
        }
    })