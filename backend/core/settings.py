"""
Django settings for digital_evidence_gap project.
"""
import os
from pathlib import Path
from urllib.parse import quote_plus
from datetime import timedelta

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')

# Allowed hosts
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Project apps
    'src.users',
    'src.evidence',
    'src.search',
    'src.common',
]

# Environment-specific apps
if DJANGO_ENV == 'development':
    INSTALLED_APPS += [
        'django_extensions',  # Useful development tools
        # 'drf_yasg',  # API documentation (commented out due to pkg_resources issue)
    ]

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For serving static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequestLoggingMiddleware',
    'core.middleware.ExceptionHandlingMiddleware',
]

# URL configuration
ROOT_URLCONF = 'core.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = 'core.wsgi.application'

# MongoDB configuration
MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'digital_evidence_gap')
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', '')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', '')

# Build MongoDB URI
def get_mongodb_uri():
    """Construct MongoDB connection URI."""
    if MONGODB_USERNAME and MONGODB_PASSWORD:
        # With authentication
        credentials = f"{quote_plus(MONGODB_USERNAME)}:{quote_plus(MONGODB_PASSWORD)}@"
        uri = f"mongodb://{credentials}{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}"
    else:
        # Without authentication (local development)
        uri = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}"

    # Add additional options for production
    if DJANGO_ENV == 'production':
        uri += "?ssl=true&replicaSet=rs0&readPreference=secondaryPreferred"

    return uri

# MongoDB connection settings
MONGODB_URI = get_mongodb_uri()

# Database configuration for Django (using SQLite for Django-specific tables)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# MongoDB collections configuration
MONGODB_COLLECTIONS = {
    'users': 'users',
    'evidence': 'evidence',
    'search_history': 'search_history',
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'src.common.pagination.CustomPagination',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'EXCEPTION_HANDLER': 'src.common.exceptions.custom_exception_handler',
}

# Environment-specific REST Framework settings
if DJANGO_ENV == 'development':
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
        'rest_framework.renderers.BrowsableAPIRenderer'
    )

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 15))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', 1))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.getenv('JWT_SECRET_KEY', SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS configuration
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000',
).split(',')
if DJANGO_ENV == 'development':
    CORS_ALLOWED_ORIGINS = list(set(CORS_ALLOWED_ORIGINS + [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:8080',
        'http://127.0.0.1:8080',
    ]))
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DJANGO_ENV == 'development' else 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': os.getenv('LOG_LEVEL', 'DEBUG' if DJANGO_ENV == 'development' else 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('LOG_LEVEL', 'DEBUG' if DJANGO_ENV == 'development' else 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': os.getenv('LOG_LEVEL', 'DEBUG' if DJANGO_ENV == 'development' else 'INFO'),
            'propagate': False,
        },
    },
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('MAX_FILE_SIZE', 104857600))  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = FILE_UPLOAD_MAX_MEMORY_SIZE
FILE_UPLOAD_TEMP_DIR = BASE_DIR / 'tmp'

# Security settings
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Production-specific security settings
if DJANGO_ENV == 'production':
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email configuration
if DJANGO_ENV == 'development':
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Cache configuration
if DJANGO_ENV == 'development':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Development-specific settings
if DJANGO_ENV == 'development':
    # Swagger/OpenAPI configuration
    SWAGGER_SETTINGS = {
        'SECURITY_DEFINITIONS': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header'
            }
        },
        'USE_SESSION_AUTH': False,
        'JSON_EDITOR': True,
        'SUPPORTED_SUBMIT_METHODS': [
            'get',
            'post',
            'put',
            'delete',
            'patch'
        ],
        'OPERATIONS_SORTER': 'alpha',
        'TAGS_SORTER': 'alpha',
        'DOC_EXPANSION': 'none',
        'DEEP_LINKING': True,
        'SHOW_EXTENSIONS': True,
        'DEFAULT_MODEL_RENDERING': 'model',
    }

    REDOC_SETTINGS = {
        'LAZY_RENDERING': False,
    }

# Production-specific settings
if DJANGO_ENV == 'production':
    # Performance optimizations
    CONN_MAX_AGE = 60  # Database connection persistence

    # Admin configuration
    ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

    # Monitoring and health checks
    HEALTH_CHECK = {
        'DISK_USAGE_MAX': 90,  # percent
        'MEMORY_MIN': 100,    # in MB
    }

    # Compression
    COMPRESS_ENABLED = True
    COMPRESS_OFFLINE = True
    COMPRESS_CSS_FILTERS = [
        'compressor.filters.css_default.CssAbsoluteFilter',
        'compressor.filters.cssmin.rCSSMinFilter',
    ]
    COMPRESS_JS_FILTERS = [
        'compressor.filters.jsmin.rJSMinFilter',
    ]

    # Security headers
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

    # Monitoring
    if os.getenv('SENTRY_DSN'):
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=os.getenv('SENTRY_DSN'),
            integrations=[DjangoIntegration()],
            environment='production',
            traces_sample_rate=1.0,
            send_default_pii=True
        )

    # Database connection pool settings for production
    MONGODB_MAX_POOL_SIZE = int(os.getenv('MONGODB_MAX_POOL_SIZE', 50))
    MONGODB_MIN_POOL_SIZE = int(os.getenv('MONGODB_MIN_POOL_SIZE', 10))
