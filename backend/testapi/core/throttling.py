# core/throttling.py - Custom throttling classes for Phase 2
"""
Custom throttling classes for enhanced API security
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
import hashlib


class LoginRateThrottle(AnonRateThrottle):
    """
    Throttle login attempts to prevent brute force attacks
    """
    scope = 'login'
    
    def get_cache_key(self, request, view):
        """
        Create cache key based on IP and username to prevent brute force
        on specific accounts from different IPs
        """
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            # Use IP + username from request data for login attempts
            ident = self.get_ident(request)
            username = request.data.get('username', '')
            if username:
                # Hash the combination of IP and username
                ident = hashlib.sha256(f"{ident}:{username}".encode()).hexdigest()
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class RegisterRateThrottle(AnonRateThrottle):
    """
    Throttle registration attempts to prevent spam accounts
    """
    scope = 'register'


class PasswordResetRateThrottle(AnonRateThrottle):
    """
    Throttle password reset attempts to prevent email spam
    """
    scope = 'password_reset'


class BurstRateThrottle(UserRateThrottle):
    """
    Allow burst of requests but limit over longer period
    """
    scope = 'burst'
    rate = '60/min'  # 60 requests per minute


class SustainedRateThrottle(UserRateThrottle):
    """
    Sustained rate limiting for general API usage
    """
    scope = 'sustained'  
    rate = '1000/hour'  # 1000 requests per hour


class CreatePostThrottle(UserRateThrottle):
    """
    Specific throttling for post creation to prevent spam
    """
    scope = 'create_post'
    rate = '10/hour'  # 10 posts per hour


class AdminActionThrottle(UserRateThrottle):
    """
    Throttle admin actions more strictly
    """
    scope = 'admin'
    rate = '100/hour'
    
    def allow_request(self, request, view):
        """
        Only apply throttling to admin users
        """
        if not request.user.is_authenticated or not request.user.is_staff:
            return True  # Don't throttle non-admin users
        return super().allow_request(request, view)