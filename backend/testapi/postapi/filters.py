import django_filters
from .models import Post


class PostFilter(django_filters.FilterSet):
    """Advanced filtering for posts"""
    
    # Text search filters
    title = django_filters.CharFilter(lookup_expr='icontains')
    body = django_filters.CharFilter(lookup_expr='icontains')
    
    # Author filters
    author = django_filters.CharFilter(field_name='author__username', lookup_expr='icontains')
    author_id = django_filters.NumberFilter(field_name='author__id')
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Content length filters
    min_word_count = django_filters.NumberFilter(method='filter_min_words')
    max_word_count = django_filters.NumberFilter(method='filter_max_words')
    
    class Meta:
        model = Post
        fields = ['is_published', 'author', 'created_at']
    
    def filter_min_words(self, queryset, name, value):
        """Filter posts with minimum word count"""
        post_ids = []
        for post in queryset:
            if post.word_count >= value:
                post_ids.append(post.id)
        return queryset.filter(id__in=post_ids)
    
    def filter_max_words(self, queryset, name, value):
        """Filter posts with maximum word count"""
        post_ids = []
        for post in queryset:
            if post.word_count <= value:
                post_ids.append(post.id)
        return queryset.filter(id__in=post_ids)
