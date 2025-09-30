from .production import *  # noqa

# Override production settings for Docker testing
DEBUG = True
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Allow all hosts for Docker testing
ALLOWED_HOSTS = ['*']

# Use console logging for Docker
import os
os.environ['LOG_TO_CONSOLE'] = '1'
os.environ['LOG_TO_FILE'] = '0'

# Re-import logging config with new environment
from config.logging import LOGGING as DOCKER_LOGGING
LOGGING = DOCKER_LOGGING
