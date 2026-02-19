from django.core.cache import cache
from django.test import TestCase

from printing.models import PrintEvent
from printing.signals import update_statistics
from tests.factories import (
    BuildingFactory,
    DepartmentFactory,
    PrinterFactory,
    PrinterModelFactory,
    PrintEventFactory,
    UserFactory,
)


class PrintingSignalsTests(TestCase):
    """Тесты для сигналов printing."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.department = DepartmentFactory(code="IT")
        self.building = BuildingFactory(code="BLD1")
        self.printer_model = PrinterModelFactory(code="HP400")
        self.printer = PrinterFactory(
            name="HP400-BLD1-IT-ROOM1-1", model=self.printer_model, building=self.building, department=self.department
        )
        self.user = UserFactory(username="testuser", department=self.department)

        # Очищаем кэш перед каждым тестом
        cache.clear()

    def test_update_statistics_on_create(self):
        """Тест обновления статистики при создании события."""
        # Создаем событие печати
        PrintEventFactory(user=self.user, printer=self.printer, pages=5, byte_size=1024)

        # Проверяем, что кэш был очищен
        # (сигнал должен был сработать автоматически)
        # Проверим это, создав еще одно событие и убедившись, что кэш очищается

        # Устанавливаем тестовые значения в кэш
        cache.set("department_stats_top", "test_data", 300)
        cache.set("user_stats_top10", "test_data", 300)

        # Создаем новое событие
        PrintEventFactory(user=self.user, printer=self.printer, pages=3, byte_size=512)

        # Проверяем, что кэш был очищен
        self.assertIsNone(cache.get("department_stats_top"))
        self.assertIsNone(cache.get("user_stats_top10"))

    def test_update_statistics_signal_receiver(self):
        """Тест прямого вызова функции сигнала."""
        # Создаем событие печати
        event = PrintEventFactory(user=self.user, printer=self.printer, pages=5, byte_size=1024)

        # Устанавливаем тестовые значения в кэш
        department_cache_key = f"print_stats_{self.user.department_id}"
        cache.set("department_stats_top", "test_data", 300)
        cache.set("user_stats_top10", "test_data", 300)
        cache.set(department_cache_key, "test_data", 300)
        cache.set("total_print_stats", "test_data", 300)

        # Вызываем функцию сигнала напрямую
        update_statistics(sender=PrintEvent, instance=event, created=True)

        # Проверяем, что кэш был очищен
        self.assertIsNone(cache.get("department_stats_top"))
        self.assertIsNone(cache.get("user_stats_top10"))
        self.assertIsNone(cache.get(department_cache_key))
        self.assertIsNone(cache.get("total_print_stats"))

    def test_update_statistics_not_created(self):
        """Тест, что сигнал не срабатывает при обновлении (не создании)."""
        # Создаем событие печати
        event = PrintEventFactory(user=self.user, printer=self.printer, pages=5, byte_size=1024)

        # Устанавливаем тестовые значения в кэш
        cache.set("department_stats_top", "test_data", 300)
        cache.set("user_stats_top10", "test_data", 300)

        # Вызываем функцию сигнала с created=False
        update_statistics(sender=PrintEvent, instance=event, created=False)

        # Проверяем, что кэш НЕ был очищен
        self.assertEqual(cache.get("department_stats_top"), "test_data")
        self.assertEqual(cache.get("user_stats_top10"), "test_data")

    def test_update_statistics_cache_keys(self):
        """Тест очистки всех ключей кэша."""
        # Создаем событие печати
        event = PrintEventFactory(user=self.user, printer=self.printer, pages=5, byte_size=1024)

        # Устанавливаем различные ключи кэша
        department_cache_key = f"print_stats_{self.user.department_id}"
        cache_keys = ["department_stats_top", "user_stats_top10", department_cache_key, "total_print_stats"]

        for key in cache_keys:
            cache.set(key, f"test_data_{key}", 300)

        # Вызываем функцию сигнала
        update_statistics(sender=PrintEvent, instance=event, created=True)

        # Проверяем, что все ключи были очищены
        for key in cache_keys:
            self.assertIsNone(cache.get(key), f"Key {key} should be cleared")
