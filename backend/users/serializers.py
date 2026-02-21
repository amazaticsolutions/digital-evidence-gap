"""
User serializers for authentication and profile management.

This module defines request/response serializers for:
- User registration (sign up)
- User authentication (sign in)
- User profile management
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSignUpSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Request fields:
        email: User email (required, unique)
        password: User password (required, min 8 chars)
        password_confirm: Password confirmation (required)
        phone_number: Phone number (optional)
        organization: Organization name (optional)
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="Password (minimum 8 characters)"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirm password"
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'phone_number',
            'organization',
        ]
        extra_kwargs = {
            'email': {'required': True},
            'phone_number': {'required': False},
            'organization': {'required': False},
        }
    
    def validate(self, attrs):
        """Validate passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })
        return attrs
    
    def create(self, validated_data):
        """Create new user with hashed password."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number', ''),
            organization=validated_data.get('organization', ''),
        )
        return user


class UserSignInSerializer(serializers.Serializer):
    """
    Serializer for user authentication.
    
    Request fields:
        email: User email (required)
        password: User password (required)
    """
    email = serializers.EmailField(
        required=True,
        help_text="User email address"
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="User password"
    )


class UserResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for user response data.
    """
    id = serializers.CharField(read_only=True)  # ObjectId as string
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone_number',
            'organization',
            'role',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer for JWT token response.
    """
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")
    user = UserResponseSerializer()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile updates.
    """
    class Meta:
        model = User
        fields = [
            'phone_number',
            'organization',
        ]