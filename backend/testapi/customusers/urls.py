
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings
from core.views import health_check
from django.conf.urls.static import static
# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

# URL patterns
urlpatterns = [
    # API routes from router
    path('', include(router.urls)),
    
    # Health check endpoint
    path('health/', health_check, name='health-check'),
]
