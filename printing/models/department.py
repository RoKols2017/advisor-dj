from django.db import models
from django.utils import timezone


class Department(models.Model):
    code = models.CharField('Код подразделения', max_length=20, unique=True)
    name = models.CharField('Название', max_length=255)
    created_at = models.DateTimeField('Дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}" 