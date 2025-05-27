from django.db import models
from django.conf import settings
from django.utils import timezone


class Computer(models.Model):
    name = models.CharField('Имя компьютера', max_length=255, unique=True)
    created_at = models.DateTimeField('Дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'Компьютер'
        verbose_name_plural = 'Компьютеры'
        ordering = ['name']

    def __str__(self):
        return self.name


class Port(models.Model):
    name = models.CharField('Название порта', max_length=255)
    created_at = models.DateTimeField('Дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'Порт'
        verbose_name_plural = 'Порты'
        ordering = ['name']

    def __str__(self):
        return self.name


class PrintEvent(models.Model):
    document_id = models.IntegerField('ID документа', db_index=True)
    document_name = models.CharField('Название документа', max_length=512)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='print_events',
        verbose_name='Пользователь'
    )
    printer = models.ForeignKey(
        'printing.Printer',
        on_delete=models.CASCADE,
        related_name='print_events',
        verbose_name='Принтер'
    )
    job_id = models.CharField('ID задания', max_length=64, db_index=True)
    timestamp = models.DateTimeField('Время печати', default=timezone.now, db_index=True)
    byte_size = models.IntegerField('Размер в байтах')
    pages = models.IntegerField('Количество страниц')
    created_at = models.DateTimeField('Дата создания', default=timezone.now)
    computer = models.ForeignKey(
        Computer,
        on_delete=models.SET_NULL,
        null=True,
        related_name='print_events',
        verbose_name='Компьютер'
    )
    port = models.ForeignKey(
        Port,
        on_delete=models.SET_NULL,
        null=True,
        related_name='print_events',
        verbose_name='Порт'
    )

    class Meta:
        verbose_name = 'Событие печати'
        verbose_name_plural = 'События печати'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['document_id']),
            models.Index(fields=['job_id']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f'{self.document_name} ({self.user})' 