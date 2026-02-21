"""
User services for authentication and profile management.

This module provides business logic for:
- User registration
- User authentication
- JWT token generation
- Profile management
"""

from typing import Optional, Dict, Any, Tuple
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def create_user(
    email: str,
    password: str,
    phone_number: str = '',
    organization: str = '',
    role: str = 'analyst'
) -> Tuple[Optional[User], Optional[str]]:
    """
    Create a new user.
    
    Args:
        email: User email
        password: User password
        phone_number: Phone number (optional)
        organization: Organization name (optional)
        role: User role (default: analyst)
    
    Returns:
        Tuple of (user, error_message)
    """
    try:
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return None, "User with this email already exists."
        
        user = User.objects.create_user(
            email=email,
            password=password,
            phone_number=phone_number,
            organization=organization,
            role=role
        )
        return user, None
    except Exception as e:
        return None, str(e)


def authenticate_user(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Authenticate a user with email and password.
    
    Args:
        email: User email
        password: User password
    
    Returns:
        Tuple of (user, error_message)
    """
    try:
        user = authenticate(email=email, password=password)
        if user is None:
            return None, "Invalid email or password."
        if not user.is_active:
            return None, "User account is disabled."
        return user, None
    except Exception as e:
        return None, str(e)


def get_tokens_for_user(user: User) -> Dict[str, str]:
    """
    Generate JWT tokens for a user.
    
    Args:
        user: User instance
    
    Returns:
        Dict with 'access' and 'refresh' tokens
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
    
    Returns:
        User instance or None
    """
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def get_user_by_email(email: str) -> Optional[User]:
    """
    Get user by email.
    
    Args:
        email: User email
    
    Returns:
        User instance or None
    """
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


def update_user_profile(
    user: User,
    phone_number: Optional[str] = None,
    organization: Optional[str] = None
) -> Tuple[User, Optional[str]]:
    """
    Update user profile.
    
    Args:
        user: User instance
        phone_number: New phone number (optional)
        organization: New organization (optional)
    
    Returns:
        Tuple of (updated_user, error_message)
    """
    try:
        if phone_number is not None:
            user.phone_number = phone_number
        if organization is not None:
            user.organization = organization
        user.save()
        return user, None
    except Exception as e:
        return user, str(e)