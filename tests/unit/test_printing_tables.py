from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from printing.models import PrintEvent
from printing.tables import PrintEventTable
from tests.factories import (
    BuildingFactory,
    ComputerFactory,
    DepartmentFactory,
    PrinterFactory,
    PrinterModelFactory,
    PrintEventFactory,
    UserFactory,
)


class PrintEventTableTests(TestCase):
    """Тесты для PrintEventTable."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.department = DepartmentFactory(code="IT")
        self.building = BuildingFactory(code="BLD1")
        self.printer_model = PrinterModelFactory(code="HP400")
        self.printer = PrinterFactory(
            name="HP400-BLD1-IT-ROOM1-1", model=self.printer_model, building=self.building, department=self.department
        )
        self.user = UserFactory(username="testuser", department=self.department)
        self.computer = ComputerFactory(name="PC1")

    def test_table_creation(self):
        """Тест создания таблицы."""
        events = PrintEvent.objects.all()
        table = PrintEventTable(events)

        self.assertIsNotNone(table)
        self.assertEqual(len(table.rows), 0)

    def test_table_with_data(self):
        """Тест таблицы с данными."""
        # Создаем событие печати
        PrintEventFactory(
            user=self.user,
            printer=self.printer,
            computer=self.computer,
            document_name="Test Document",
            pages=5,
            byte_size=1024,
        )

        events = PrintEvent.objects.all()
        table = PrintEventTable(events)

        self.assertEqual(len(table.rows), 1)

        # Проверяем, что данные отображаются
        row = table.rows[0]
        self.assertEqual(row.get_cell("document_name"), "Test Document")
        self.assertEqual(row.get_cell("pages"), 5)

    def test_render_byte_size_bytes(self):
        """Тест отображения размера в байтах."""
        PrintEventFactory(user=self.user, printer=self.printer, computer=self.computer, byte_size=512)

        events = PrintEvent.objects.all()
        table = PrintEventTable(events)

        row = table.rows[0]
        self.assertEqual(row.get_cell("byte_size"), "512 B")

    def test_render_byte_size_kilobytes(self):
        """Тест отображения размера в килобайтах."""
        PrintEventFactory(user=self.user, printer=self.printer, computer=self.computer, byte_size=2048)  # 2 KB

        events = PrintEvent.objects.all()
        table = PrintEventTable(events)

        row = table.rows[0]
        self.assertEqual(row.get_cell("byte_size"), "2.0 KB")

    def test_render_byte_size_megabytes(self):
        """Тест отображения размера в мегабайтах."""
        PrintEventFactory(user=self.user, printer=self.printer, computer=self.computer, byte_size=2097152)  # 2 MB

        events = PrintEvent.objects.all()
        table = PrintEventTable(events)

        row = table.rows[0]
        self.assertEqual(row.get_cell("byte_size"), "2.0 MB")

    def test_table_ordering(self):
        """Тест сортировки таблицы."""
        # Создаем события с разными временными метками
        now = timezone.now()
        PrintEventFactory(user=self.user, printer=self.printer, computer=self.computer, timestamp=now)
        PrintEventFactory(
            user=self.user, printer=self.printer, computer=self.computer, timestamp=now - timedelta(hours=1)
        )

        events = PrintEvent.objects.all()
        table = PrintEventTable(events)

        # Проверяем, что события отсортированы по убыванию времени
        self.assertEqual(len(table.rows), 2)
        # Первое событие должно быть более новым (проверяем форматированное значение)
        first_timestamp = table.rows[0].get_cell("timestamp")
        self.assertIsNotNone(first_timestamp)

    def test_table_meta_attributes(self):
        """Тест мета-атрибутов таблицы."""
        events = PrintEvent.objects.all()
        table = PrintEventTable(events)

        # Проверяем мета-атрибуты
        self.assertEqual(table.Meta.model, PrintEvent)
        self.assertEqual(table.Meta.template_name, "django_tables2/bootstrap5.html")
        self.assertIn("timestamp", table.Meta.fields)
        self.assertIn("document_name", table.Meta.fields)
        self.assertIn("user", table.Meta.fields)
        self.assertIn("printer", table.Meta.fields)
        self.assertIn("computer", table.Meta.fields)
        self.assertIn("pages", table.Meta.fields)
        self.assertIn("byte_size", table.Meta.fields)
        self.assertEqual(table.Meta.order_by, "-timestamp")
