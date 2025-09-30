from __future__ import annotations

from typing import Optional
from django.contrib.auth import get_user_model

User = get_user_model()


def get_or_create_user_by_username(username: str, *, fio: Optional[str] = None, is_active: bool = True) -> User:
    normalized = (username or "").strip().lower()
    if not normalized:
        raise ValueError("username is empty")
    user = User.objects.filter(username__iexact=normalized).first()
    if user:
        return user
    return User.objects.create(username=normalized, fio=fio or normalized, is_active=is_active)


