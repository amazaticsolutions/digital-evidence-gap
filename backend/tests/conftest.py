"""
Pytest configuration and fixtures for digital_evidence_gap.
"""
import os
import django
from django.conf import settings

# Setup Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Configure Django settings for testing if not already configured
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key-for-testing-only',
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'rest_framework',
            'rest_framework_simplejwt',
            'corsheaders',
            'apps.users',
            'apps.evidence',
            'apps.search',
            'apps.common',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        USE_TZ=True,
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'rest_framework_simplejwt.authentication.JWTAuthentication',
            ],
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.IsAuthenticated',
            ],
        },
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'corsheaders.middleware.CorsMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'core.middleware.RequestLoggingMiddleware',
            'core.middleware.ExceptionHandlingMiddleware',
        ],
    )

django.setup()

import pytest
from django.test import RequestFactory
from rest_framework.test import APIClient


@pytest.fixture
def request_factory():
    """Provide a Django RequestFactory instance."""
    return RequestFactory()


@pytest.fixture
def api_client():
    """Provide a Django REST Framework APIClient instance."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Provide an authenticated API client."""
    # This would need to be implemented once user authentication is set up
    # For now, return the regular client
    return api_client


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests."""
    import logging
    logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing."""
    return {
        'email': 'test@example.com',
        'password': 'testpass123'
    }


@pytest.fixture
def sample_evidence_data():
    """Provide sample evidence data for testing."""
    return {
        'title': 'Test Evidence',
        'file_type': 'image/jpeg',
        'drive_file_id': '1abc123def456',
        'drive_url': 'https://drive.google.com/file/d/1abc123def456/view',
        'uploaded_by': 'user123',
    }


@pytest.fixture
def sample_search_data():
    """Provide sample search data for testing."""
    return {
        'user_id': 'user123',
        'query': 'test evidence',
        'filters': {'file_type': 'image'},
        'searched_at': '2024-01-01T12:00:00Z'
    }