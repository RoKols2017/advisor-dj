import os

LOG_DIR = os.getenv('LOG_DIR', './logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_TO_FILE = os.getenv('LOG_TO_FILE', '1') != '0'
LOG_TO_CONSOLE = os.getenv('LOG_TO_CONSOLE', '1') != '0'
LOG_FILE_NAME = os.getenv('LOG_FILE_NAME', 'project.log')

handlers = {}
root_handlers = []

if LOG_TO_FILE:
    handlers['file'] = {
        'level': 'INFO',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': os.path.join(LOG_DIR, LOG_FILE_NAME),
        'maxBytes': 5*1024*1024,
        'backupCount': 5,
        'formatter': 'default',
        'encoding': 'utf-8',
    }
    root_handlers.append('file')
if LOG_TO_CONSOLE:
    handlers['console'] = {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'default',
    }
    root_handlers.append('console')
if not root_handlers:
    handlers['null'] = {
        'class': 'logging.NullHandler',
    }
    root_handlers = ['null']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': handlers,
    'root': {
        'handlers': root_handlers,
        'level': 'INFO',
    },
} 