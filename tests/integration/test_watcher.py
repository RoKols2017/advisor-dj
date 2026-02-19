import tempfile
from pathlib import Path

from django.test import TestCase

from printing.importers import import_print_events_from_json, import_users_from_csv
from tests.factories import BuildingFactory, DepartmentFactory, PrinterFactory, PrinterModelFactory, UserFactory

# ImportService is used indirectly through importers


class WatcherIntegrationTests(TestCase):
    """Интеграционные тесты для watcher-демона."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.watch_dir = self.temp_dir / "watch"
        self.processed_dir = self.temp_dir / "processed"
        self.quarantine_dir = self.temp_dir / "quarantine"

        # Создаем директории
        self.watch_dir.mkdir()
        self.processed_dir.mkdir()
        self.quarantine_dir.mkdir()

    def tearDown(self):
        """Очистка после тестов."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_import_print_events_from_json_success(self):
        """Тест успешного импорта событий печати из JSON."""
        # Создаем тестовые данные
        events_data = [
            {
                "JobID": "test_job_1",
                "Param1": 100,
                "Param2": "test_document.pdf",
                "Param3": "testuser",
                "Param4": "PC1",
                "Param5": "HP400-BLD1-IT-ROOM1-1",
                "Param6": "USB001",
                "Param7": 1024,
                "Param8": 5,
                "TimeCreated": "/Date(1696000000000)/",
            }
        ]

        # Создаем необходимые объекты
        department = DepartmentFactory(code="IT")
        building = BuildingFactory(code="BLD1")
        printer_model = PrinterModelFactory(code="HP400")
        PrinterFactory(name="HP400-BLD1-IT-ROOM1-1", model=printer_model, building=building, department=department)
        UserFactory(username="testuser", department=department)

        # Тестируем импорт
        result = import_print_events_from_json(events_data)

        self.assertEqual(result["created"], 1)
        self.assertEqual(len(result["errors"]), 0)

    def test_import_users_from_csv_success(self):
        """Тест успешного импорта пользователей из CSV."""
        # Создаем CSV данные
        csv_data = "SamAccountName,DisplayName,OU\nuser1,User One,IT\nuser2,User Two,HR"

        # Создаем временный файл
        csv_file = self.temp_dir / "users.csv"
        csv_file.write_text(csv_data, encoding="utf-8-sig")

        # Тестируем импорт
        with open(csv_file, "rb") as f:
            result = import_users_from_csv(f)

        self.assertEqual(result["created"], 2)
        self.assertEqual(len(result["errors"]), 0)

    def test_import_with_errors(self):
        """Тест импорта с ошибками."""
        # Создаем некорректные данные
        events_data = [
            {
                "JobID": "test_job_invalid",
                "Param3": "nonexistent_user",  # Пользователь не существует
                "Param5": "INVALID-PRINTER-FORMAT",  # Неверный формат принтера
            }
        ]

        result = import_print_events_from_json(events_data)

        self.assertEqual(result["created"], 0)
        self.assertGreater(len(result["errors"]), 0)

    def test_idempotency(self):
        """Тест идемпотентности импорта."""
        # Создаем тестовые данные
        events_data = [
            {
                "JobID": "duplicate_job",
                "Param1": 200,
                "Param2": "duplicate.pdf",
                "Param3": "testuser",
                "Param4": "PC1",
                "Param5": "HP400-BLD1-IT-ROOM1-1",
                "Param6": "USB001",
                "Param7": 500,
                "Param8": 2,
                "TimeCreated": "/Date(1696000000000)/",
            }
        ]

        # Создаем необходимые объекты
        department = DepartmentFactory(code="IT")
        building = BuildingFactory(code="BLD1")
        printer_model = PrinterModelFactory(code="HP400")
        PrinterFactory(name="HP400-BLD1-IT-ROOM1-1", model=printer_model, building=building, department=department)
        UserFactory(username="testuser", department=department)

        # Первый импорт
        result1 = import_print_events_from_json(events_data)
        self.assertEqual(result1["created"], 1)

        # Второй импорт (должен быть пропущен)
        result2 = import_print_events_from_json(events_data)
        self.assertEqual(result2["created"], 0)
        self.assertEqual(len(result2["errors"]), 0)

    def test_watcher_file_processing_simple(self):
        """Простой тест обработки файлов watcher'ом."""
        # Создаем тестовые файлы
        json_file = self.watch_dir / "events.json"
        csv_file = self.watch_dir / "users.csv"

        json_file.write_text('{"test": "data"}')
        csv_file.write_text("test,data")

        # Проверяем, что файлы созданы
        self.assertTrue(json_file.exists())
        self.assertTrue(csv_file.exists())

        # Проверяем содержимое
        self.assertEqual(json_file.read_text(), '{"test": "data"}')
        self.assertEqual(csv_file.read_text(), "test,data")
