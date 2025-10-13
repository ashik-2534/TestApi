"""
Maintenance Mode Middleware
Returns 503 Service Unavailable during database reset operations
"""
import os
from django.http import JsonResponse


class MaintenanceMiddleware:
    """
    Middleware to handle maintenance mode during database resets.
    When a lock file exists, returns 503 responses to all requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.lock_file = '/tmp/reset_in_progress'
    
    def __call__(self, request):
        # Check if maintenance lock file exists
        if os.path.exists(self.lock_file):
            return JsonResponse(
                {
                    'detail': 'Service is currently resetting. Please try again in a few moments.',
                    'status': 'maintenance',
                    'code': 503
                },
                status=503
            )
        
        response = self.get_response(request)
        return response