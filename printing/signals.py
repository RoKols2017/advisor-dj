from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PrintEvent


@receiver(post_save, sender=PrintEvent)
def update_statistics(sender, instance, created, **kwargs):
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
        cache.delete(f'print_stats_{instance.user.department.id}')
        cache.delete('total_print_stats')
        cache.delete('department_stats_top')
        cache.delete('user_stats_top10')