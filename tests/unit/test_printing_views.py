from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from printing.models import Department, Building, PrinterModel, Printer, PrintEvent
from tests.factories import DepartmentFactory, BuildingFactory, PrinterModelFactory, PrinterFactory, UserFactory, PrintEventFactory

User = get_user_model()


class PrintingViewsTests(TestCase):
    """Тесты для views модуля printing."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = Client()
        
        # Создаем пользователя
        self.department = DepartmentFactory(code='IT')
        self.user = UserFactory(username='testuser', department=self.department)
        self.user.set_password('testpass')
        self.user.save()
        
        # Создаем принтер и события печати
        self.building = BuildingFactory(code='BLD1')
        self.printer_model = PrinterModelFactory(code='HP400')
        self.printer = PrinterFactory(
            name='HP400-BLD1-IT-ROOM1-1',
            model=self.printer_model,
            building=self.building,
            department=self.department,
            cost_per_page=Decimal('2.00')
        )
        
        # Создаем события печати
        self.print_event = PrintEventFactory(
            user=self.user,
            printer=self.printer,
            pages=5,
            timestamp=timezone.now()
        )

    def test_dashboard_view_authenticated(self):
        """Тест dashboard для аутентифицированного пользователя."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        # Проверяем, что страница содержит основные элементы
        self.assertContains(response, 'Панель управления')
        self.assertContains(response, 'Всего страниц')

    def test_dashboard_view_unauthenticated(self):
        """Тест dashboard для неаутентифицированного пользователя."""
        response = self.client.get('/')
        
        # Должен быть редирект на страницу входа
        self.assertEqual(response.status_code, 302)

    def test_print_events_view_authenticated(self):
        """Тест страницы событий печати."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/events/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'События печати')

    def test_statistics_view_authenticated(self):
        """Тест страницы статистики."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/statistics/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Статистика')

    def test_print_tree_view_authenticated(self):
        """Тест страницы дерева печати."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/tree/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Дерево событий')

    def test_print_tree_view_with_dates(self):
        """Тест страницы дерева печати с фильтрацией по датам."""
        self.client.login(username='testuser', password='testpass')
        
        # Тестируем с параметрами дат
        response = self.client.get('/tree/', {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31'
        })
        
        self.assertEqual(response.status_code, 200)

    def test_import_users_view_get(self):
        """Тест GET запроса страницы импорта пользователей."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/import/users/')
        
        self.assertEqual(response.status_code, 200)

    def test_import_users_view_post_no_file(self):
        """Тест POST запроса без файла."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post('/import/users/')
        
        # Должен вернуть 200 с ошибкой в контексте
        self.assertEqual(response.status_code, 200)

    def test_import_users_view_post_invalid_file(self):
        """Тест POST запроса с неверным файлом."""
        self.client.login(username='testuser', password='testpass')
        
        # Создаем временный файл с неправильным расширением
        with open('/tmp/test.txt', 'w') as f:
            f.write('test data')
        
        with open('/tmp/test.txt', 'rb') as f:
            response = self.client.post('/import/users/', {'file': f})
        
        # Должен вернуть 200 с ошибкой в контексте
        self.assertEqual(response.status_code, 200)

    def test_import_print_events_view_get(self):
        """Тест GET запроса страницы импорта событий печати."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/import/print-events/')
        
        self.assertEqual(response.status_code, 200)

    def test_import_print_events_view_post_json(self):
        """Тест POST запроса с JSON данными."""
        self.client.login(username='testuser', password='testpass')
        
        events_data = [
            {
                "JobID": "test_job",
                "Param1": 100,
                "Param2": "test.pdf",
                "Param3": "testuser",
                "Param4": "PC1",
                "Param5": "HP400-BLD1-IT-ROOM1-1",
                "Param6": "USB001",
                "Param7": 1024,
                "Param8": 5,
                "TimeCreated": "/Date(1696000000000)/"
            }
        ]
        
        response = self.client.post(
            '/import/print-events/',
            data=str(events_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)

    def test_user_info_view(self):
        """Тест страницы информации о пользователе."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/user-info/')
        
        self.assertEqual(response.status_code, 200)
