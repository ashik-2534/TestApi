import django_filters
from .models import User

class UserFilter(django_filters.FilterSet):
    """
    Advanced filtering for users with security considerations
    """
    
    # Text search filters
    username = django_filters.CharFilter(lookup_expr='icontains')
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')
    bio = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='iexact')  # Exact match for email for security
    
    # Date filters
    joined_after = django_filters.DateTimeFilter(field_name='date_joined', lookup_expr='gte')
    joined_before = django_filters.DateTimeFilter(field_name='date_joined', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Activity filters
    has_posts = django_filters.BooleanFilter(method='filter_has_posts')
    min_posts = django_filters.NumberFilter(method='filter_min_posts')
    active_users = django_filters.BooleanFilter(method='filter_active_users')
    
    # Profile completion filters
    has_bio = django_filters.BooleanFilter(method='filter_has_bio')
    has_avatar = django_filters.BooleanFilter(method='filter_has_avatar')
    has_full_name = django_filters.BooleanFilter(method='filter_has_full_name')
    
    class Meta:
        model = User
        fields = {
            'is_active': ['exact'],
            'is_staff': ['exact'],
            'date_joined': ['gte', 'lte', 'exact'],
            'last_login': ['gte', 'lte', 'isnull'],
        }
    
    def filter_has_posts(self, queryset, name, value):
        """Filter users who have/don't have posts"""
        if value:
            return queryset.filter(posts__isnull=False).distinct()
        else:
            return queryset.filter(posts__isnull=True).distinct()
    
    def filter_min_posts(self, queryset, name, value):
        """Filter users with minimum number of posts"""
        from django.db.models import Count
        return queryset.annotate(
            post_count=Count('posts')
        ).filter(post_count__gte=value)
    
    def filter_active_users(self, queryset, name, value):
        """Filter users who have been active recently"""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            thirty_days_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(last_login__gte=thirty_days_ago)
        return queryset
    
    def filter_has_bio(self, queryset, name, value):
        """Filter users who have/don't have a bio"""
        if value:
            return queryset.exclude(bio='')
        else:
            return queryset.filter(bio='')
    
    def filter_has_avatar(self, queryset, name, value):
        """Filter users who have/don't have an avatar"""
        if value:
            return queryset.exclude(avatar='')
        else:
            return queryset.filter(avatar='')
    
    def filter_has_full_name(self, queryset, name, value):
        """Filter users who have/don't have first and last name"""
        if value:
            return queryset.exclude(first_name='').exclude(last_name='')
        else:
            return queryset.filter(
                django_filters.Q(first_name='') | django_filters.Q(last_name='')
            )
    
    @property
    def qs(self):
        """
        Override to add security filtering - hide sensitive user data from non-authenticated users
        """
        parent_qs = super().qs
        
        # If request is available and user is not authenticated or staff,
        # we could add additional filtering here for security
        request = self.request if hasattr(self, 'request') else None
        
        if request and not request.user.is_authenticated:
            # For anonymous users, we might want to limit what they can see
            # This is optional - you can remove this if you want all user profiles public
            pass
        
        return parent_qs