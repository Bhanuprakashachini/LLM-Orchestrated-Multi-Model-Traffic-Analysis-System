"""
Django settings for traffic_analysis project.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver').split(',')

# Application definition - MongoDB-only apps
DJANGO_APPS = [
    # Remove Django apps that require database tables
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    # 'django.contrib.contenttypes',  # DISABLED - causes auth dependencies
    # 'django.contrib.sessions',
    # 'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    # 'rest_framework_simplejwt',  # DISABLED - causes Django auth dependency
    'corsheaders',
    'channels',
    'drf_spectacular',
    'django_filters',
]

LOCAL_APPS = [
    'apps.authentication',  # Uses MongoDB for auth
    'apps.analysis',        # Uses MongoDB for analysis data
    'apps.streaming',       # Uses MongoDB for streaming data
    'apps.llm_integration', # Uses MongoDB for LLM data
    'apps.analytics',       # Uses MongoDB for analytics
    'apps.users',          # Uses MongoDB for user data
    'apps.traffic_violations',  # Traffic violation detection (file-based storage)
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # 'django.contrib.sessions.middleware.SessionMiddleware',  # Disabled - no sessions
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',  # Disabled - using MongoDB auth
    # 'django.contrib.messages.middleware.MessageMiddleware',  # Disabled - no messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'traffic_analysis.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                # 'django.contrib.auth.context_processors.auth',  # DISABLED - Django auth
                # 'django.contrib.messages.context_processors.messages',  # DISABLED - Django messages
            ],
        },
    },
]

WSGI_APPLICATION = 'traffic_analysis.wsgi.application'
ASGI_APPLICATION = 'traffic_analysis.asgi.application'

# Database - Using MongoDB only (no SQLite)
# Dummy database configuration to satisfy Django requirements
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy',
        'NAME': ':memory:',
    }
}

# MongoDB Configuration using PyMongo
MONGODB_SETTINGS = {
    'host': config('MONGO_HOST', default='localhost'),
    'port': int(config('MONGO_PORT', default='27017')),
    'database': config('MONGO_DB_NAME', default='traffic_analysis_db'),
    'username': config('MONGO_USERNAME', default=''),
    'password': config('MONGO_PASSWORD', default=''),
    'auth_source': config('MONGO_AUTH_SOURCE', default='admin'),
}

# MongoDB URI for direct connection
MONGODB_URI = config('MONGODB_URI', default='mongodb://localhost:27017/')
MONGODB_DB_NAME = config('MONGO_DB_NAME', default='traffic_analysis_db')

# Redis Configuration for Channels and Celery
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
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
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration - MongoDB-only mode
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.authentication.mongo_jwt_auth.MongoJWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',  # DISABLED - requires Django sessions
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Changed to AllowAny to avoid Django auth
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Disable Django auth completely
    'UNAUTHENTICATED_USER': None,
    'UNAUTHENTICATED_TOKEN': None,
}

# JWT Configuration - Using custom MongoDB JWT
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
#     'ROTATE_REFRESH_TOKENS': True,
#     'BLACKLIST_AFTER_ROTATION': True,
# }

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# CORS Configuration
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', 
    default='http://localhost:3002,http://127.0.0.1:3002,http://localhost:3001,http://127.0.0.1:3001,http://localhost:3000,http://127.0.0.1:3000'
).split(',')

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  # Temporary fix for testing
CORS_ALLOWED_HEADERS = [
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

# Allow CORS for media files
CORS_URLS_REGEX = r'^/(api|media)/.*$'

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Traffic Analysis API',
    'DESCRIPTION': 'AI-powered traffic scene perception and analysis system',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Logging Configuration - Suppress development server warnings
import logging

# Disable Django's development server warning and 404 warnings
logging.getLogger('django.server').setLevel(logging.ERROR)
logging.getLogger('django.request').setLevel(logging.ERROR)
logging.getLogger('django.utils.autoreload').setLevel(logging.ERROR)

# Suppress Django system check warnings
SILENCED_SYSTEM_CHECKS = [
    'urls.W002',  # URL pattern warnings
    'models.W042',  # Auto-created primary key warnings
    'admin.E408',  # Admin warnings
    'admin.E409',  # Admin warnings
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,  # Disable all existing loggers
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',  # Only show errors
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.utils.autoreload': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'ERROR',
    },
}

# Suppress Django development server warnings at the system level
import warnings
warnings.filterwarnings('ignore', message='.*development server.*')

# AI Model Configuration
YOLO_MODEL_PATH = config('YOLO_MODEL_PATH', default=os.path.join(BASE_DIR, 'models', 'yolov8s.pt'))
YOLO_DEVICE = config('YOLO_DEVICE', default='cpu')

# Model directory
MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# LLM Configuration
LLM_SETTINGS = {
    'PROVIDER': config('LLM_PROVIDER', default='groq'),
    'OPENAI_API_KEY': config('OPENAI_API_KEY', default=''),
    'ANTHROPIC_API_KEY': config('ANTHROPIC_API_KEY', default=''),
    'GROQ_API_KEY': config('GROQ_API_KEY', default=''),
    'GROQ_MODEL': config('GROQ_MODEL', default='gpt-oss-20b'),
    'GROQ_BACKUP_MODEL': config('GROQ_BACKUP_MODEL', default='llama-3.1-70b-versatile'),
    'GROQ_FALLBACK_MODEL': config('GROQ_FALLBACK_MODEL', default='llama-3.1-8b-instant'),
    'GROQ_MAX_TOKENS': config('GROQ_MAX_TOKENS', default=1000, cast=int),
    'GROQ_TEMPERATURE': config('GROQ_TEMPERATURE', default=0.7, cast=float),
    'GROQ_TOP_P': config('GROQ_TOP_P', default=0.9, cast=float),
    'MAX_TOKENS': 1000,
    'TEMPERATURE': 0.7,
}

# Make LLM settings available as individual settings
LLM_PROVIDER = LLM_SETTINGS['PROVIDER']
GROQ_API_KEY = LLM_SETTINGS['GROQ_API_KEY']
GROQ_MODEL = LLM_SETTINGS['GROQ_MODEL']
GROQ_BACKUP_MODEL = LLM_SETTINGS['GROQ_BACKUP_MODEL']
GROQ_FALLBACK_MODEL = LLM_SETTINGS['GROQ_FALLBACK_MODEL']
GROQ_MAX_TOKENS = LLM_SETTINGS['GROQ_MAX_TOKENS']
GROQ_TEMPERATURE = LLM_SETTINGS['GROQ_TEMPERATURE']
GROQ_TOP_P = LLM_SETTINGS['GROQ_TOP_P']

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Security Settings for Production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True