from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from customusers.models import User


class Post(models.Model):
    """
    Post model for blog-like functionality
    Each post belongs to a user (author)
    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        help_text="The user who created the post",
    )
    title = models.CharField(max_length=200, help_text="Post title")
    slug = models.SlugField(
        unique=True, max_length=255, help_text="URL friendly verbose of title"
    )
    body = models.TextField(help_text="Post content")
    excerpt = models.CharField(
        max_length=300, blank=True, help_text="Short description of the post"
    )
    featured_image = models.URLField(blank=True, help_text="Featured image url")
    is_published = models.BooleanField(default=True , help_text="Wheater this post is publicly visible ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_published"]),
            models.Index(fields=["author"])
        ]
        
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Auto generate title if not provided"""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            # Ensuers unique slug
            while Post.objects.filter(slug=slug).exists:
                slug = f"{base_slug}-{counter}"
                counter += 1
        
            self.slug = slug
        # Auto generate excerpt from body if not provided
        if not self.excerpt and self.body:
            self.excerpt = self.body[:297] + "..." if len(self.body) > 300 else self.body
            
        super().save(*args, **kwargs)
    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'slug': self.slug})
    
    @property
    def word_count(self):
        return len(self.body.split())
    
    @property
    def read_time(self):
        """Estimate reading time in minutes (assuming 200 words per minute)"""
        return max(1, self.word_count // 200)

