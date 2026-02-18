import os
from pathlib import Path
from urllib.parse import unquote_plus, urlparse

from config.logging import LOGGING as PROJECT_LOGGING

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key")
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]
IMPORT_TOKEN = os.getenv("IMPORT_TOKEN", "")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.AccountsConfig',
    'printing.apps.PrintingConfig',
    'django_bootstrap5',
    'import_export',
    'django_tables2',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',
    'django.contrib.humanize',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


def _db_from_env():
    # Сначала проверяем отдельные переменные окружения (приоритет)
    postgres_db = os.getenv('POSTGRES_DB')
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_host = os.getenv('POSTGRES_HOST')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    
    if postgres_db and postgres_user:
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': postgres_db,
            'USER': postgres_user,
            'PASSWORD': postgres_password or '',
            'HOST': postgres_host or 'localhost',
            'PORT': postgres_port,
        }
    
    # Fallback на DATABASE_URL (для обратной совместимости)
    url = os.getenv('DATABASE_URL')
    if not url:
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    
    parsed = urlparse(url)
    if parsed.scheme.startswith('postgres'):
        # Декодируем пароль, если он был закодирован
        password = unquote_plus(parsed.password or '') if parsed.password else ''
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path.lstrip('/'),
            'USER': parsed.username or '',
            'PASSWORD': password,
            'HOST': parsed.hostname or 'localhost',
            'PORT': str(parsed.port or '5432'),
        }
    if parsed.scheme.startswith('sqlite'):
        db_path = parsed.path if parsed.path else '/db.sqlite3'
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / db_path.lstrip('/'),
        }
    raise ValueError('Unsupported DATABASE_URL')


DATABASES = {
    'default': _db_from_env()
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

LOGGING = PROJECT_LOGGING
