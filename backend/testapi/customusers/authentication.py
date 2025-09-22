
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, ScopedRateThrottle
from .serializers import UserSerializer, UserCreateSerializer
import logging
from django.utils import timezone
from django.conf import settings


# Setup logging for security events
logger = logging.getLogger('customusers')

# Custom Throttling Classes for Phase 2
class LoginRateThrottle(AnonRateThrottle):
    """Throttle login attempts to prevent brute force attacks"""
    scope = 'login'

class RegisterRateThrottle(AnonRateThrottle):
    """Throttle registration attempts to prevent spam accounts"""
    scope = 'register'


class PasswordResetRateThrottle(AnonRateThrottle):
    """Throttle password reset attempts"""
    scope = 'password_reset'

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes user data in the response
    Enhanced JWT serializer with additional security features and logging
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to token for better security
        token['username'] = user.username
        token['email'] = user.email
        token['user_id'] = user.id
        token['is_staff'] = user.is_staff
        token['login_time'] = timezone.now().isoformat()
        
        return token
    
    def validate(self, attrs):
        # Log login attempt
        username = attrs.get('username')
        ip_address = self.context['request'].META.get('REMOTE_ADDR', 'unknown')
        logger.info(f"Login attempt for username: {username} from IP: {ip_address}")
        
        try:
            # Get the standard token data
            data = super().validate(attrs)
            
            # Add user information to response
            user_serializer = UserSerializer(self.user)
            data['user'] = user_serializer.data
            
            # Update last login
            self.user.last_login = timezone.now()
            self.user.save(update_fields=['last_login'])
            
            # Log successful login
            logger.info(f"Successful login for user: {self.user.username} (ID: {self.user.id})")
            
            return data
            
        except Exception as e:
            # Log failed login attempt for security monitoring
            logger.warning(f"Failed login attempt for username: {username} from IP: {ip_address} - Error: {str(e)}")
            raise


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Enhanced token view with throttling and security logging
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]


class CustomTokenRefreshView(TokenRefreshView):
    """
    Enhanced token refresh view with logging
    """
    def post(self, request, *args, **kwargs):
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        logger.info(f"Token refresh attempt from IP: {ip_address}")
        
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            logger.info("Token refresh successful")
        else:
            logger.warning(f"Token refresh failed from IP: {ip_address}")
            
        return response


# Phase 2: Enhanced Authentication Endpoints with Security Features
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register(request):
    """
    Enhanced user registration with rate limiting and security logging
    """
    # Extract and log registration attempt details
    username = request.data.get('username', 'unknown')
    email = request.data.get('email', 'unknown')
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    
    logger.info(f"Registration attempt - Username: {username}, Email: {email}, IP: {ip_address}")
    
    # Validate request data
    serializer = UserCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Create user
            user = serializer.save()
            
            # Generate tokens for the new user
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            # Add custom claims to access token
            access['username'] = user.username
            access['email'] = user.email
            access['user_id'] = user.id
            access['login_time'] = timezone.now().isoformat()
            
            user_data = UserSerializer(user).data
            
            # Log successful registration
            logger.info(f"User registered successfully - ID: {user.id}, Username: {user.username}, IP: {ip_address}")
            
            return Response({
                'message': 'User registered successfully',
                'user': user_data,
                'tokens': {
                    'access': str(access),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Registration error for {username}: {str(e)}")
            return Response({
                'error': 'Registration failed due to server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log validation errors for security monitoring
    logger.warning(f"Registration validation failed for {username} from IP {ip_address}: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    """
    Enhanced login with security features, rate limiting, and comprehensive logging
    """
    username_or_email = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    # Input validation with security logging
    if not username_or_email or not password:
        logger.warning(f"Login attempt with missing credentials from IP: {ip_address}")
        return Response({
            'error': 'Username/email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Log the login attempt
    logger.info(f"Login attempt for: {username_or_email} from IP: {ip_address}")
    
    user = None
    
    try:
        # Try to authenticate with username first, then email
        user = authenticate(username=username_or_email, password=password)
        
        if not user:
            # Try with email
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user_obj = User.objects.get(email=username_or_email, is_active=True)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user and user.is_active:
            # Generate tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            # Add custom claims
            access['username'] = user.username
            access['email'] = user.email
            access['user_id'] = user.id
            access['login_time'] = timezone.now().isoformat()
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            user_data = UserSerializer(user).data
            
            # Log successful login
            logger.info(f"Successful login for user: {user.username} (ID: {user.id}) from IP: {ip_address}")
            
            return Response({
                'message': 'Login successful',
                'user': user_data,
                'tokens': {
                    'access': str(access),
                    'refresh': str(refresh),
                }
            })
        else:
            # Log failed attempt without revealing if user exists (prevent username enumeration)
            logger.warning(f"Failed login attempt for: {username_or_email} from IP: {ip_address}, User-Agent: {user_agent}")
            
    except Exception as e:
        logger.error(f"Login error for {username_or_email} from IP {ip_address}: {str(e)}")
    
    # Generic error message to prevent username enumeration attacks
    return Response({
        'error': 'Invalid credentials or inactive account'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@throttle_classes([UserRateThrottle])
def logout(request):
    """
    Enhanced logout with token blacklisting and security logging
    """
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    username = request.user.username if request.user.is_authenticated else 'anonymous'
    
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"User logged out: {username} from IP: {ip_address}")
            return Response({'message': 'Successfully logged out'})
        else:
            logger.warning(f"Logout attempt without refresh token from IP: {ip_address}")
            return Response({
                'error': 'Refresh token required'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.warning(f"Logout error for {username} from IP {ip_address}: {str(e)}")
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def verify_token(request):
    """
    Enhanced token verification with detailed response
    """
    if not request.user.is_authenticated:
        return Response({
            'valid': False,
            'error': 'Token invalid or expired'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    user_data = UserSerializer(request.user).data
    return Response({
        'valid': True,
        'user': user_data,
        'token_info': {
            'user_id': request.user.id,
            'username': request.user.username,
            'is_staff': request.user.is_staff,
            'last_login': request.user.last_login.isoformat() if request.user.last_login else None,
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])  # Custom throttle class for this endpoint
def refresh_token(request):
    """
    Enhanced custom refresh token endpoint with security logging
    """
    refresh_token = request.data.get('refresh')
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    
    if not refresh_token:
        logger.warning(f"Token refresh attempt without refresh token from IP: {ip_address}")
        return Response({
            'error': 'Refresh token required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken(refresh_token)
        access = refresh.access_token
        
        # Add custom claims to new access token
        user_id = refresh.payload.get('user_id')
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                access['username'] = user.username
                access['email'] = user.email
                access['user_id'] = user.id
                access['refresh_time'] = timezone.now().isoformat()
                
                logger.info(f"Token refreshed successfully for user: {user.username} from IP: {ip_address}")
            except User.DoesNotExist:
                logger.warning(f"Token refresh failed - user not found for ID: {user_id}")
        
        return Response({
            'access': str(access),
            'refresh': str(refresh)
        })
        
    except Exception as e:
        logger.warning(f"Token refresh failed from IP {ip_address}: {str(e)}")
        return Response({
            'error': 'Invalid refresh token'
        }, status=status.HTTP_401_UNAUTHORIZED)


# Phase 2: Additional Security Endpoints
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def request_password_reset(request):
    """
    Password reset request with enhanced security and rate limiting
    """
    email = request.data.get('email', '').strip()
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(email=email, is_active=True)
        
        # Log password reset request
        logger.info(f"Password reset requested for user: {user.username} from IP: {ip_address}")
        
        # In a real implementation, you would:
        # 1. Generate a secure token
        # 2. Store it with expiration
        # 3. Send email with reset link
        
        return Response({
            'message': 'If an account with this email exists, you will receive password reset instructions.'
        })
        
    except User.DoesNotExist:
        # Don't reveal if email exists or not (prevent email enumeration)
        logger.warning(f"Password reset requested for non-existent email: {email} from IP: {ip_address}")
        return Response({
            'message': 'If an account with this email exists, you will receive password reset instructions.'
        })


@api_view(['GET'])
def security_status(request):
    """
    Get security status information (admin only)
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return Response({
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        'debug_mode': settings.DEBUG,
        'secret_key_configured': bool(settings.SECRET_KEY and settings.SECRET_KEY != 'default_secret_key'),
        'jwt_configured': bool(settings.SIMPLE_JWT),
        'cors_configured': bool(getattr(settings, 'CORS_ALLOWED_ORIGINS', [])),
        'throttling_enabled': bool(settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_CLASSES')),
        'database_type': settings.DATABASES['default']['ENGINE'],
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'jwt_access_lifetime': str(settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME')),
        'jwt_refresh_lifetime': str(settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME')),
    })