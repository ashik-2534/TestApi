from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Post
from customusers.serializers import UserSerializer

class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for Post model with author information
    Used for listing and retrieving posts
    """
    author = UserSerializer(read_only=True)
    word_count = serializers.ReadOnlyField()
    read_time = serializers.ReadOnlyField()
    
    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'slug',
            'body',
            'excerpt',
            'featured_image',
            'is_published',
            'author',
            'word_count',
            'read_time',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'author']


class PostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating posts
    Excludes author field as it will be set automatically
    """
    class Meta:
        model = Post
        fields = [
            'title',
            'slug',  # Optional - will auto-generate if not provided
            'body',
            'excerpt',
            'featured_image',
            'is_published'
        ]
        extra_kwargs = {
            'slug': {'required': False},
            'excerpt': {'required': False},
            'featured_image': {'required': False},
            'is_published': {'default': True}
        }


class PostUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating posts
    Same as create but may have different validation rules in future
    """
    class Meta:
        model = Post
        fields = [
            'title',
            'slug',
            'body',
            'excerpt',
            'featured_image',
            'is_published'
        ]
        extra_kwargs = {
            'slug': {'required': False},
            'excerpt': {'required': False},
            'featured_image': {'required': False}
        }


class PostListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing posts
    Excludes full body content for better performance
    """
    author = serializers.StringRelatedField()  # Just shows username
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'featured_image',
            'author',
            'author_id',
            'is_published',
            'created_at',
            'read_time'
        ]


class PostDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual post view
    Includes full author information and all post data
    """
    author = UserSerializer(read_only=True)
    word_count = serializers.ReadOnlyField()
    read_time = serializers.ReadOnlyField()
    
    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'slug',
            'body',
            'excerpt',
            'featured_image',
            'is_published',
            'author',
            'word_count',
            'read_time',
            'created_at',
            'updated_at'
        ]

