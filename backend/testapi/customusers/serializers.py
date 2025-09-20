from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    Used for displaying user information in API responses
    """
    full_name = serializers.ReadOnlyField()
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name',
            'full_name',
            'bio', 
            'avatar',
            'posts_count',
            'date_joined',
            'is_active'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active']
    
    def get_posts_count(self, obj):
        """Get the number of published posts by this user"""
        return obj.posts.filter(is_published=True).count()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    Includes password handling and validation
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username',
            'email', 
            'first_name', 
            'last_name',
            'bio',
            'avatar',
            'password',
            'password_confirm'
        ]
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop('password_confirm')
        
        # Create user with hashed password
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    Excludes sensitive fields like username and email
    """
    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name',
            'bio', 
            'avatar'
        ]



# Authentication Serializers
class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    Will be used with JWT authentication
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate that new passwords match"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        """Validate that old password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value