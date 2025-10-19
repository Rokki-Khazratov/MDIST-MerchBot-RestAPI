"""
Custom middleware for request logging.
"""
import time
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Middleware to log all HTTP requests to console.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Start timing
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = round((time.time() - start_time) * 1000, 2)
        
        # Log request
        status_color = self._get_status_color(response.status_code)
        method_color = self._get_method_color(request.method)
        
        print(f"🌐 {request.method} {request.path} - {status_color}{response.status_code}{' ' * (3 - len(str(response.status_code)))} ({duration}ms)")
        
        return response
    
    def _get_status_color(self, status_code):
        """Get color for status code."""
        if 200 <= status_code < 300:
            return f'\033[92m{status_code}\033[0m'  # Green
        elif 300 <= status_code < 400:
            return f'\033[93m{status_code}\033[0m'  # Yellow
        elif 400 <= status_code < 500:
            return f'\033[91m{status_code}\033[0m'  # Red
        elif 500 <= status_code < 600:
            return f'\033[95m{status_code}\033[0m'  # Magenta
        else:
            return str(status_code)
    
    def _get_method_color(self, method):
        """Get color for HTTP method."""
        colors = {
            'GET': '\033[94m',      # Blue
            'POST': '\033[92m',     # Green
            'PUT': '\033[93m',      # Yellow
            'PATCH': '\033[96m',    # Cyan
            'DELETE': '\033[91m',   # Red
        }
        return colors.get(method, '\033[97m')  # White default
