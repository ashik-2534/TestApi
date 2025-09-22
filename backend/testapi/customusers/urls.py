
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings
from core.views import health_check
from . import authentication
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf.urls.static import static
# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

# URL patterns
urlpatterns = [
    # API routes from router
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/login/', authentication.login, name='auth-login'),
    path('auth/register/', authentication.register, name='auth-register'),
    path('auth/logout/', authentication.logout, name='auth-logout'),
    path('auth/verify/', authentication.verify_token, name='auth-verify'),
    path('auth/refresh/', authentication.refresh_token, name='auth-refresh'),
    
    
    #New security endpoints
    path('auth/password-reset/', authentication.request_password_reset, name='auth-password-reset'),
    path('auth/security-status/', authentication.security_status, name='auth-security-status'),
    
    
    # JWT Token endpoints (alternative URLs for compatibility)
    path('token/', authentication.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Health check endpoint
    path('health/', health_check, name='health-check'),
]
