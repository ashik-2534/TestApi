from django.contrib import admin
from .models import User, Post
# Register your models here.


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Post Admin"""
    list_display = ('title', 'author', 'is_published', 'created_at', 'word_count')
    list_filter = ('is_published', 'created_at', 'author')
    search_fields = ('title', 'body', 'author__username')
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'author', 'body', 'excerpt')
        }),
        ('Media', {
            'fields': ('featured_image',),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('is_published',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        """Auto-set author to current user if creating new post"""
        if not change:  # Creating new post
            obj.author = request.user
        super().save_model(request, obj, form, change)