from django.utils import timezone

def site_settings(request):
    return {
        'current_year': timezone.now().year,
        'site_name': 'Smart Life Analyzer',
        'site_description': 'Track, analyze, and improve your daily life',
    }