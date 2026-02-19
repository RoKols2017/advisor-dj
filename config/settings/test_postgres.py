from .test import *  # noqa
from .base import _db_from_env


DATABASES = {
    "default": _db_from_env(),  # noqa: F405
}
