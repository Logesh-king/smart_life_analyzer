from django.utils import timezone
from datetime import timedelta
from .models import DailyEntry, Suggestion
from django.db.models import Avg, Sum, Count, Q

def calculate_stats(entries):
    """
    Calculate aggregate statistics for a queryset of DailyEntry.
    """
    if not entries.exists():
        return {
            'avg_sleep': 0,
            'total_work': 0,
            'total_expense': 0,
            'mood_distribution': {},
            'most_common_mood': DailyEntry.Mood.NEUTRAL
        }
    
    # Calculate aggregates in a single query where possible
    aggregates = entries.aggregate(
        avg_sleep=Avg('sleep_hours'),
        total_work=Sum('work_hours'),
        total_expense=Sum('expense')
    )
    
    avg_sleep = aggregates['avg_sleep'] or 0
    total_work = aggregates['total_work'] or 0
    total_expense = aggregates['total_expense'] or 0
    
    # Get mood distribution efficiently
    mood_counts = entries.values('mood').annotate(count=Count('mood')).order_by('-count')
    mood_dist = {item['mood']: item['count'] for item in mood_counts}
    most_common_mood = mood_counts[0]['mood'] if mood_counts else DailyEntry.Mood.NEUTRAL
    
    return {
        'avg_sleep': round(avg_sleep, 1),
        'total_work': round(total_work, 1),
        'total_expense': round(total_expense, 2),
        'mood_distribution': mood_dist,
        'most_common_mood': most_common_mood
    }

def get_suggestion_data(user):
    """
    Generate a list of suggestion dictionaries based on user data.
    """
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    entries = DailyEntry.objects.filter(
        user=user, 
        date__range=[start_date, today]
    )
    
    if not entries.exists():
        return []
    
    # Use centralized stats calculation
    stats = calculate_stats(entries)
    avg_sleep = stats['avg_sleep']
    # Average work per day needs to be calculated from total work / days with entries
    # But for now sticking to the original logic which seemed to imply daily average
    # To be precise: original used Avg('work_hours'), calculate_stats uses Sum. 
    # Let's fix calculate_stats to also return averages if needed or just use current query
    
    # Re-evaluating: Original code used Avg for sleep, Avg for work, Avg for expense.
    # calculate_stats returned Sum for work and expense. 
    # Let's adjust calculate_stats to be more flexible or just compute averages here.
    
    # Actually, let's stick to the original logic's requirement:
    avg_work = entries.aggregate(Avg('work_hours'))['work_hours__avg'] or 0
    avg_expense = entries.aggregate(Avg('expense'))['expense__avg'] or 0
    
    most_common_mood = stats['most_common_mood']
    
    suggestions = []
    
    # Sleep suggestions
    if avg_sleep < 6:
        suggestions.append({
            'category': Suggestion.Category.SLEEP,
            'priority': Suggestion.Priority.CRITICAL,
            'title': 'Insufficient Sleep Detected',
            'description': f'Your average sleep is only {avg_sleep:.1f} hours. Aim for 7-9 hours for optimal health and productivity.',
            'icon': 'bed',
            'confidence': 85
        })
    elif avg_sleep > 9:
        suggestions.append({
            'category': Suggestion.Category.SLEEP,
            'priority': Suggestion.Priority.WARNING,
            'title': 'Excessive Sleep Alert',
            'description': f'Your average sleep is {avg_sleep:.1f} hours. While rest is important, excessive sleep can lead to fatigue.',
            'icon': 'clock',
            'confidence': 70
        })
    elif 7 <= avg_sleep <= 8:
        suggestions.append({
            'category': Suggestion.Category.SLEEP,
            'priority': Suggestion.Priority.GOOD,
            'title': 'Optimal Sleep Pattern',
            'description': f'Great! Your average sleep of {avg_sleep:.1f} hours is in the healthy range.',
            'icon': 'check-circle',
            'confidence': 90
        })
    
    # Work suggestions
    if avg_work > 10:
        suggestions.append({
            'category': Suggestion.Category.WORK,
            'priority': Suggestion.Priority.CRITICAL,
            'title': 'Work Overload Alert',
            'description': f'You\'re averaging {avg_work:.1f} work hours daily. Consider taking breaks to prevent burnout.',
            'icon': 'briefcase',
            'confidence': 90
        })
    elif avg_work < 4:
        suggestions.append({
            'category': Suggestion.Category.WORK,
            'priority': Suggestion.Priority.WARNING,
            'title': 'Low Productivity Hours',
            'description': f'Your average work hours are {avg_work:.1f}. Try to maintain consistent productivity.',
            'icon': 'chart-line',
            'confidence': 65
        })
    
    # Expense suggestions
    if avg_expense > 50:
        suggestions.append({
            'category': Suggestion.Category.FINANCE,
            'priority': Suggestion.Priority.CRITICAL,
            'title': 'High Daily Expenses',
            'description': f'Your average daily expense is ${avg_expense:.2f}. Consider tracking specific categories.',
            'icon': 'wallet',
            'confidence': 80
        })
    elif avg_expense < 20:
        suggestions.append({
            'category': Suggestion.Category.FINANCE,
            'priority': Suggestion.Priority.GOOD,
            'title': 'Good Expense Management',
            'description': f'Great job managing expenses! Your average is ${avg_expense:.2f} per day.',
            'icon': 'piggy-bank',
            'confidence': 85
        })
    
    # Mood suggestions
    if most_common_mood in [DailyEntry.Mood.SAD, DailyEntry.Mood.STRESSED, DailyEntry.Mood.ANGRY]:
        suggestions.append({
            'category': Suggestion.Category.MOOD,
            'priority': Suggestion.Priority.WARNING,
            'title': 'Mood Improvement Opportunity',
            'description': 'Your mood data suggests room for improvement. Consider mindfulness or exercise.',
            'icon': 'smile',
            'confidence': 75
        })
    
    return suggestions

def generate_suggestions(user):
    """Generate and save AI-style suggestions based on user data"""
    # Clear old active suggestions
    Suggestion.objects.filter(user=user, is_active=True).update(is_active=False)
    
    suggestions_data = get_suggestion_data(user)
    
    # Create suggestion records
    new_suggestions = []
    for data in suggestions_data:
        # Filter out keys not in the model (like 'icon', 'confidence')
        model_data = {k: v for k, v in data.items() if k in ['category', 'priority', 'title', 'description']}
        new_suggestions.append(Suggestion(user=user, **model_data))
    
    # Bulk create for performance
    Suggestion.objects.bulk_create(new_suggestions)
    
    return suggestions_data

def calculate_analytics(user):
    """Calculate and store analytics data"""
    today = timezone.now().date()
    
    # Weekly analytics
    week_start = today - timedelta(days=today.weekday())
    week_entries = DailyEntry.objects.filter(
        user=user,
        date__range=[week_start, today]
    )
    
    return calculate_stats(week_entries) if week_entries.exists() else None