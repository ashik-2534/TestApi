
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from customusers import views as userview
from postapi import views as postview
from django.conf import settings
from .views import health_check
from django.conf.urls.static import static
# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', userview.UserViewSet, basename='user')
router.register(r'posts', postview.PostViewSet, basename='post')

# URL patterns
urlpatterns = [
    # API routes from router
    path('', include(router.urls)),
    
    # Health check endpoint
    path('health/', health_check, name='health-check'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
