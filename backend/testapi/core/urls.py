
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('config/', admin.site.urls),
    path('users/',include('customusers.urls')),
    path('posts/',include('postapi.urls')),
]
