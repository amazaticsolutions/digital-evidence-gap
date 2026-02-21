"""Users models"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    
    # Additional fields can be added here
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username
