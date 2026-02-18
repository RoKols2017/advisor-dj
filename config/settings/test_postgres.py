from .base import _db_from_env
from .test import *  # noqa


DATABASES = {
    'default': _db_from_env(),  # noqa: F405
}
