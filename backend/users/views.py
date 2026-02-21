"""
User views for authentication and profile management API.

API Endpoints:
    POST   /api/users/signup/     - Register a new user
    POST   /api/users/signin/     - Authenticate and get JWT tokens
    POST   /api/users/refresh/    - Refresh JWT access token
    GET    /api/users/me/         - Get current user profile
    PATCH  /api/users/me/         - Update current user profile
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    UserSignUpSerializer,
    UserSignInSerializer,
    UserResponseSerializer,
    TokenResponseSerializer,
    UserProfileSerializer,
)
from . import services


class SignUpView(APIView):
    """
    Register a new user account.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a new user account",
        request_body=UserSignUpSerializer,
        responses={
            201: TokenResponseSerializer,
            400: 'Validation error',
        },
        tags=['Authentication']
    )
    def post(self, request):
        """Create a new user account."""
        serializer = UserSignUpSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = serializer.save()
        
        # Generate tokens
        tokens = services.get_tokens_for_user(user)
        
        return Response({
            "access": tokens['access'],
            "refresh": tokens['refresh'],
            "user": UserResponseSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class SignInView(APIView):
    """
    Authenticate user and get JWT tokens.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Authenticate user and get JWT tokens",
        request_body=UserSignInSerializer,
        responses={
            200: TokenResponseSerializer,
            400: 'Validation error',
            401: 'Invalid credentials',
        },
        tags=['Authentication']
    )
    def post(self, request):
        """Authenticate and return tokens."""
        serializer = UserSignInSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Authenticate user
        user, error = services.authenticate_user(email, password)
        
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate tokens
        tokens = services.get_tokens_for_user(user)
        
        return Response({
            "access": tokens['access'],
            "refresh": tokens['refresh'],
            "user": UserResponseSerializer(user).data
        }, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    Get or update current user profile.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current user profile",
        responses={
            200: UserResponseSerializer,
            401: 'Not authenticated',
        },
        tags=['Users']
    )
    def get(self, request):
        """Get current user profile."""
        return Response(
            UserResponseSerializer(request.user).data,
            status=status.HTTP_200_OK
        )
    
    @swagger_auto_schema(
        operation_description="Update current user profile",
        request_body=UserProfileSerializer,
        responses={
            200: UserResponseSerializer,
            400: 'Validation error',
            401: 'Not authenticated',
        },
        tags=['Users']
    )
    def patch(self, request):
        """Update current user profile."""
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        
        return Response(
            UserResponseSerializer(request.user).data,
            status=status.HTTP_200_OK
        )