from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from ..models import PrintEvent, Department, User, Printer

class PrintEventTests(TestCase):
    """
    Тесты для модели PrintEvent.

    Methods:
        setUp(): Подготовка данных для тестов
        test_print_event_creation(): Тест создания события
        test_get_cost(): Тест расчета стоимости
        test_get_department(): Тест получения отдела

    Example:
        >>> python manage.py test printing.tests.test_models
    """

    def setUp(self):
        """Подготовка данных для тестов."""
        self.department = Department.objects.create(
            name='Test Department',
            code='TEST'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            department=self.department
        )
        self.printer = Printer.objects.create(
            name='Test Printer',
            cost_per_page=Decimal('2.00')
        )

    def test_print_event_creation(self):
        """Тест создания события печати."""
        event = PrintEvent.objects.create(
            user=self.user,
            printer=self.printer,
            pages=5,
            timestamp=timezone.now()
        )
        self.assertEqual(event.pages, 5)
        self.assertEqual(event.user, self.user)

    def test_get_cost(self):
        """Тест расчета стоимости печати."""
        event = PrintEvent.objects.create(
            user=self.user,
            printer=self.printer,
            pages=5,
            timestamp=timezone.now()
        )
        self.assertEqual(event.get_cost(), Decimal('10.00')) 