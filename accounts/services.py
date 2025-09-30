from __future__ import annotations

import logging
from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import transaction

from printing.models import Department

User = get_user_model()
logger = logging.getLogger(__name__)


class UserService:
    """
    Сервис для инкапсуляции бизнес-логики, связанной с пользователями.
    """

    @staticmethod
    def create_or_update_user(
        username: str,
        fio: str,
        department_code: str,
        is_active: bool = True
    ) -> Tuple[User, bool]:
        """
        Создает или обновляет пользователя, а также связанный отдел.
        """
        with transaction.atomic():
            department, created_dept = Department.objects.get_or_create(
                code__iexact=department_code,
                defaults={'code': department_code.upper(), 'name': department_code.upper()}
            )
            if created_dept:
                logger.info(f"Создан новый отдел: {department.name}")

            user, created_user = User.objects.update_or_create(
                username__iexact=username,
                defaults={
                    'username': username,
                    'fio': fio,
                    'department': department,
                    'is_active': is_active
                }
            )
            if created_user:
                logger.info(f"Создан новый пользователь: {user.username}")
            else:
                logger.info(f"Обновлен пользователь: {user.username}")

            return user, created_user

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """
        Получает пользователя по имени пользователя (case-insensitive).
        """
        return User.objects.filter(username__iexact=username).first()


def get_or_create_user_by_username(username: str, *, fio: str | None = None, is_active: bool = True) -> User:
    normalized = (username or "").strip().lower()
    if not normalized:
        raise ValueError("username is empty")
    user = User.objects.filter(username__iexact=normalized).first()
    if user:
        return user
    return User.objects.create(username=normalized, fio=fio or normalized, is_active=is_active)


