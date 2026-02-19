from django.db import models
from django.utils import timezone


class Building(models.Model):
    code = models.CharField("Код здания", max_length=10, unique=True)
    name = models.CharField("Название", max_length=255)
    created_at = models.DateTimeField("Дата создания", default=timezone.now)

    class Meta:
        verbose_name = "Здание"
        verbose_name_plural = "Здания"
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"
