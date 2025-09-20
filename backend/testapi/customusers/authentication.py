
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .serializers import UserSerializer, UserCreateSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes user data in the response
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to token
        token['username'] = user.username
        token['email'] = user.email
        token['user_id'] = user.id
        
        return token
    
    def validate(self, attrs):
        # Get the standard token data
        data = super().validate(attrs)
        
        # Add user information to response
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that returns user data along with tokens
    """
    serializer_class = CustomTokenObtainPairSerializer


# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user and return JWT tokens
    """
    serializer = UserCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate tokens for the new user
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        # Add custom claims
        access['username'] = user.username
        access['email'] = user.email
        access['user_id'] = user.id
        
        user_data = UserSerializer(user).data
        
        return Response({
            'message': 'User registered successfully',
            'user': user_data,
            'tokens': {
                'access': str(access),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user with username/email and password
    Returns JWT tokens and user data
    """
    username_or_email = request.data.get('username')
    password = request.data.get('password')
    
    if not username_or_email or not password:
        return Response({
            'error': 'Username/email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Try to authenticate with username first, then email
    user = authenticate(username=username_or_email, password=password)
    
    if not user:
        # Try with email
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user_obj = User.objects.get(email=username_or_email)
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
        
        user_data = UserSerializer(user).data
        
        return Response({
            'message': 'Login successful',
            'user': user_data,
            'tokens': {
                'access': str(access),
                'refresh': str(refresh),
            }
        })
    
    return Response({
        'error': 'Invalid credentials or inactive account'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout(request):
    """
    Logout user by blacklisting the refresh token
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'})
        else:
            return Response({
                'error': 'Refresh token required'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def verify_token(request):
    """
    Verify if the current access token is valid
    Returns user data if valid
    """
    user_data = UserSerializer(request.user).data
    return Response({
        'valid': True,
        'user': user_data
    })


# JWT Token Blacklist Management
@api_view(['POST'])
def refresh_token(request):
    """
    Custom refresh token endpoint with additional validation
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
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
            except User.DoesNotExist:
                pass
        
        return Response({
            'access': str(access),
            'refresh': str(refresh)
        })
        
    except Exception as e:
        return Response({
            'error': 'Invalid refresh token'
        }, status=status.HTTP_401_UNAUTHORIZED)