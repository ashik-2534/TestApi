from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import PostFilter
from django.db.models import Q

from .models import Post
from .serializers import (
    PostSerializer,
    PostCreateSerializer,
    PostUpdateSerializer,
    PostListSerializer,
    PostDetailSerializer
)



class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post operations
    Provides CRUD operations with proper permissions:
    - Anyone can read posts
    - Only authenticated users can create posts  
    - Only post authors can update/delete their posts
    """
    queryset = Post.objects.filter(is_published=True).order_by('-created_at')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PostFilter
    search_fields = ['title', 'body', 'excerpt']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    lookup_field = 'slug'  # Use slug instead of id in URLs
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PostListSerializer
        elif self.action == 'create':
            return PostCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PostUpdateSerializer
        elif self.action == 'retrieve':
            return PostDetailSerializer
        return PostSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions
        - Anonymous users: only published posts
        - Authenticated users: published posts + their own drafts
        """
        queryset = Post.objects.all().order_by('-created_at')
        
        if not self.request.user.is_authenticated:
            # Anonymous users only see published posts
            return queryset.filter(is_published=True)
        
        # Authenticated users see published posts + their own posts (including drafts)
        return queryset.filter(
            Q(is_published=True) | Q(author=self.request.user)
        )
    
    def perform_create(self, serializer):
        """Set the author to the current user when creating a post"""
        serializer.save(author=self.request.user)
    
    def get_permissions(self):
        """
        Set permissions based on action:
        - Anyone can read posts
        - Authenticated users can create posts
        - Only authors can update/delete their posts
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_posts(self, request):
        """Get current user's posts (including drafts)"""
        posts = self.request.user.posts.all().order_by('-created_at')
        
        # Apply pagination
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get most recent published posts"""
        recent_posts = self.get_queryset().filter(is_published=True)[:10]
        serializer = PostListSerializer(recent_posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_publish(self, request, slug=None):
        """Toggle post publish status (author only)"""
        post = self.get_object()
        
        # Check if user is the author
        if post.author != request.user:
            return Response(
                {'error': 'You can only toggle publish status of your own posts'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        post.is_published = not post.is_published
        post.save()
        
        status_text = 'published' if post.is_published else 'unpublished'
        return Response({'message': f'Post {status_text} successfully'})


# Custom Permission Classes
class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a post to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the author of the post.
        return obj.author == request.user
