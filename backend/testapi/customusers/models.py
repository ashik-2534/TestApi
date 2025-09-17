from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.text import slugify


class User (AbstractUser):
    """ 
    Custom user model for extending AbstractUser
    Adds additional fields for api functionality
    """
    
    bio = models.TextField(max_length=500, blank=True, help_text="A short bio for the user")
    avatar = models.URLField(blank=True, help_text="Profile picture url")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_name = "auth_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        
    def __str__(self):
        return self.username
    
    @property
    def full_name (self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    
