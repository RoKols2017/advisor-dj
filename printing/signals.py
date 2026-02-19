from typing import Any

from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PrintEvent
from .services import STATS_CACHE_VERSION_KEY


@receiver(post_save, sender=PrintEvent)  # type: ignore[misc]
def update_statistics(sender: type[PrintEvent], instance: PrintEvent, created: bool, **kwargs: Any) -> None:
    """
    Обновляет статистику после создания события печати.

    Args:
        sender (Model): Модель, отправившая сигнал
        instance (PrintEvent): Экземпляр события печати
        created (bool): Флаг создания нового объекта
        **kwargs: Дополнительные аргументы

    Example:
        >>> event = PrintEvent.objects.create(...)
        # Сигнал автоматически вызовется после сохранения
    """
    if created:
        # Очищаем кэш статистики
        if instance.user.department_id is not None:
            cache.delete(f"print_stats_{instance.user.department_id}")
        cache.delete("total_print_stats")
        cache.delete("department_stats_top")
        cache.delete("user_stats_top10")
        # Глобальная инвалидация всех date-specific ключей статистики.
        try:
            cache.incr(STATS_CACHE_VERSION_KEY)
        except ValueError:
            cache.set(STATS_CACHE_VERSION_KEY, 1, None)
