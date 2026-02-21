"""User models for the application."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django_mongodb_backend.fields import ObjectIdField
from .managers import UserManager


class User(AbstractUser):
    """
    Custom user model that uses email as the username field.
    """
    # id = ObjectIdField(primary_key=True, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True)
    
    # Profile fields
    phone_number = models.CharField(max_length=20, blank=True)
    organization = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=50, default='analyst')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email