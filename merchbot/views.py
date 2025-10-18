"""
Main project views (health check, etc.)
"""
from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    """
    Health check endpoint.
    
    GET /health/
    
    Returns:
        200 OK: Service is healthy
    """
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
    })

