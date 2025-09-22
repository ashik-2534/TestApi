"""
Core views for error handling and general API utilities
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
import logging

logger = logging.getLogger('django')


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint for monitoring
    """
    return Response({
        'status': 'healthy',
        'message': 'API Hub is running',
        'version': '1.0.0',
        'debug_mode': settings.DEBUG,
        'environment': 'development' if settings.DEBUG else 'production'
    })


# Custom Error Handlers for Phase 2 Security
def bad_request(request, exception=None):
    """
    Custom 400 error handler
    """
    logger.warning(f"400 Bad Request: {request.path} from IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    return JsonResponse({
        'error': 'Bad Request',
        'message': 'The request could not be understood by the server',
        'status_code': 400,
        'path': request.path
    }, status=400)


def permission_denied(request, exception=None):
    """
    Custom 403 error handler with security logging
    """
    user = getattr(request, 'user', None)
    username = user.username if user and user.is_authenticated else 'anonymous'
    
    logger.warning(f"403 Permission Denied: {request.path} for user: {username} from IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    return JsonResponse({
        'error': 'Permission Denied',
        'message': 'You do not have permission to access this resource',
        'status_code': 403,
        'path': request.path
    }, status=403)


def not_found(request, exception=None):
    """
    Custom 404 error handler
    """
    logger.info(f"404 Not Found: {request.path} from IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    return JsonResponse({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status_code': 404,
        'path': request.path
    }, status=404)


def server_error(request):
    """
    Custom 500 error handler with security considerations
    """
    logger.error(f"500 Internal Server Error: {request.path} from IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    # Don't expose sensitive information in production
    message = 'An unexpected error occurred'
    if settings.DEBUG:
        message += '. Check the server logs for more details.'
    
    return JsonResponse({
        'error': 'Internal Server Error',
        'message': message,
        'status_code': 500,
        'path': request.path
    }, status=500)


def csrf_failure(request, reason=""):
    """
    Custom CSRF failure handler
    """
    logger.warning(f"CSRF failure: {reason} for {request.path} from IP: {request.META.get('REMOTE_ADDR', 'unknown')}")
    
    return JsonResponse({
        'error': 'CSRF Verification Failed',
        'message': 'CSRF token missing or incorrect',
        'status_code': 403,
        'path': request.path
    }, status=403)