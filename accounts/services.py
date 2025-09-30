from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import transaction

from printing.models import Department

User = get_user_model()
logger = logging.getLogger(__name__)


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _normalize_department_code(code: str) -> str:
    return (code or "").strip().lower()


@dataclass
class EnsureUserResult:
    user: Any
    created: bool


@transaction.atomic
def ensure_user(username: str, fio: str | None, department_code: str) -> EnsureUserResult:
    """Создаёт/обновляет пользователя и его отдел по коду (case-insensitive)."""
    uname = _normalize_username(username)
    if not uname:
        raise ValueError("username is required")

    code = _normalize_department_code(department_code)
    if not code:
        raise ValueError("department_code is required")

    dept = Department.objects.filter(code__iexact=code).first()
    if not dept:
        dept = Department.objects.create(code=code, name=code.upper())

    user, created = User.objects.update_or_create(
        username=uname,
        defaults={
            "fio": (fio or uname),
            "department": dept,
            "is_active": True,
        },
    )
    return EnsureUserResult(user=user, created=created)


class UserService:
    """Сервис для операций с пользователями."""

    @staticmethod
    @transaction.atomic
    def create_or_update_user(
        username: str,
        fio: str,
        department_code: str,
        is_active: bool = True,
    ) -> Tuple[Any, bool]:
        uname = _normalize_username(username)
        if not uname:
            raise ValueError("username is required")
        code = _normalize_department_code(department_code)
        if not code:
            raise ValueError("department_code is required")

        dept = Department.objects.filter(code__iexact=code).first()
        if not dept:
            dept = Department.objects.create(code=code, name=code.upper())
            logger.info("Создан новый отдел: %s", dept.name)

        user, created = User.objects.update_or_create(
            username=uname,
            defaults={
                "fio": (fio or uname),
                "department": dept,
                "is_active": is_active,
            },
        )
        logger.info("%s пользователь: %s", "Создан" if created else "Обновлён", user.username)
        return user, created

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Any]:
        uname = _normalize_username(username)
        if not uname:
            return None
        return User.objects.filter(username__iexact=uname).first()


def get_or_create_user_by_username(
    username: str, *, fio: str | None = None, is_active: bool = True
) -> Any:
    uname = _normalize_username(username)
    if not uname:
        raise ValueError("username is empty")
    user = User.objects.filter(username__iexact=uname).first()
    if user:
        return user
    return User.objects.create(username=uname, fio=fio or uname, is_active=is_active)


