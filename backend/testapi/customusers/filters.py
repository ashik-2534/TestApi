import django_filters
from .models import Post, User

class UserFilter(django_filters.FilterSet):
    """Advanced filtering for users"""
    
    username = django_filters.CharFilter(lookup_expr='icontains')
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')
    bio = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date filters
    joined_after = django_filters.DateTimeFilter(field_name='date_joined', lookup_expr='gte')
    joined_before = django_filters.DateTimeFilter(field_name='date_joined', lookup_expr='lte')
    
    # Activity filters
    has_posts = django_filters.BooleanFilter(method='filter_has_posts')
    min_posts = django_filters.NumberFilter(method='filter_min_posts')
    
    class Meta:
        model = User
        fields = ['is_active', 'date_joined']
    
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