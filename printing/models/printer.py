from django.db import models
from django.utils import timezone


class PrinterModel(models.Model):
    code = models.CharField('Код модели', max_length=50, unique=True)
    manufacturer = models.CharField('Производитель', max_length=100)
    model = models.CharField('Модель', max_length=50)
    is_color = models.BooleanField('Цветной', default=False)
    is_duplex = models.BooleanField('Двусторонняя печать', default=False)
    created_at = models.DateTimeField('Дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'Модель принтера'
        verbose_name_plural = 'Модели принтеров'
        ordering = ['manufacturer', 'model']

    def __str__(self):
        return f"{self.manufacturer} {self.model}"


class Printer(models.Model):
    name = models.CharField('Название принтера', max_length=255)
    model = models.ForeignKey(
        PrinterModel,
        on_delete=models.PROTECT,
        related_name='printers',
        verbose_name='Модель принтера'
    )
    building = models.ForeignKey(
        'printing.Building',
        on_delete=models.PROTECT,
        related_name='printers',
        verbose_name='Здание'
    )
    department = models.ForeignKey(
        'printing.Department',
        on_delete=models.PROTECT,
        related_name='printers',
        verbose_name='Отдел'
    )
    room_number = models.CharField('Номер помещения', max_length=10)
    printer_index = models.IntegerField('Индекс принтера')
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'Принтер'
        verbose_name_plural = 'Принтеры'
        ordering = ['name']
        unique_together = [['building', 'room_number', 'printer_index']]

    def __str__(self):
        return f"{self.name} ({self.model})" 