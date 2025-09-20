from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'API Hub is running',
        'version': '1.0.0'
    })


# Error Handlers
def bad_request(request, exception=None):
    """Custom 400 error handler"""
    return JsonResponse({
        'error': 'Bad Request',
        'message': 'The request could not be understood by the server',
        'status_code': 400
    }, status=400)

def permission_denied(request, exception=None):
    """Custom 403 error handler"""
    return JsonResponse({
        'error': 'Permission Denied',
        'message': 'You do not have permission to access this resource',
        'status_code': 403
    }, status=403)

def not_found(request, exception=None):
    """Custom 404 error handler"""
    return JsonResponse({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status_code': 404
    }, status=404)

def server_error(request):
    """Custom 500 error handler"""
    return JsonResponse({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }, status=500)