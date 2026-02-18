from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from printing.filters import PrintEventFilter
from printing.models import PrintEvent
from tests.factories import (
    BuildingFactory,
    ComputerFactory,
    DepartmentFactory,
    PrinterFactory,
    PrinterModelFactory,
    PrintEventFactory,
    UserFactory,
)


class PrintEventFilterTests(TestCase):
    """Тесты для PrintEventFilter."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.department = DepartmentFactory(code='IT')
        self.building = BuildingFactory(code='BLD1')
        self.printer_model = PrinterModelFactory(code='HP400')
        self.printer = PrinterFactory(
            name='HP400-BLD1-IT-ROOM1-1',
            model=self.printer_model,
            building=self.building,
            department=self.department
        )
        self.user = UserFactory(username='testuser', department=self.department)
        self.computer = ComputerFactory(name='PC1')
        
        # Создаем события печати с разными датами
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        
        self.event_today = PrintEventFactory(
            user=self.user,
            printer=self.printer,
            computer=self.computer,
            document_name='Today Document',
            timestamp=timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        )
        
        self.event_yesterday = PrintEventFactory(
            user=self.user,
            printer=self.printer,
            computer=self.computer,
            document_name='Yesterday Document',
            timestamp=timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
        )
        
        self.event_last_week = PrintEventFactory(
            user=self.user,
            printer=self.printer,
            computer=self.computer,
            document_name='Last Week Document',
            timestamp=timezone.make_aware(timezone.datetime.combine(last_week, timezone.datetime.min.time()))
        )

    def test_filter_by_document_name(self):
        """Тест фильтрации по названию документа."""
        qs = PrintEvent.objects.all()
        filter_data = {'document_name': 'Today'}
        
        filtered_qs = PrintEventFilter(filter_data, queryset=qs).qs
        
        self.assertEqual(filtered_qs.count(), 1)
        self.assertEqual(filtered_qs.first(), self.event_today)

    def test_filter_by_department(self):
        """Тест фильтрации по отделу."""
        qs = PrintEvent.objects.all()
        filter_data = {'user__department': self.department.id}
        
        filtered_qs = PrintEventFilter(filter_data, queryset=qs).qs
        
        self.assertEqual(filtered_qs.count(), 3)

    def test_filter_by_printer(self):
        """Тест фильтрации по принтеру."""
        qs = PrintEvent.objects.all()
        filter_data = {'printer': self.printer.id}
        
        filtered_qs = PrintEventFilter(filter_data, queryset=qs).qs
        
        self.assertEqual(filtered_qs.count(), 3)

    def test_filter_by_computer(self):
        """Тест фильтрации по компьютеру."""
        qs = PrintEvent.objects.all()
        filter_data = {'computer': self.computer.id}
        
        filtered_qs = PrintEventFilter(filter_data, queryset=qs).qs
        
        self.assertEqual(filtered_qs.count(), 3)

    def test_filter_by_date_range(self):
        """Тест фильтрации по диапазону дат."""
        qs = PrintEvent.objects.all()
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        filter_data = {
            'timestamp_after': yesterday,
            'timestamp_before': today
        }
        
        filtered_qs = PrintEventFilter(filter_data, queryset=qs).qs
        
        # Должны получить события за вчера и сегодня (3 события из setUp)
        self.assertEqual(filtered_qs.count(), 3)

    def test_filter_combined(self):
        """Тест комбинированной фильтрации."""
        qs = PrintEvent.objects.all()
        filter_data = {
            'document_name': 'Today',
            'printer': self.printer.id
        }
        
        filtered_qs = PrintEventFilter(filter_data, queryset=qs).qs
        
        self.assertEqual(filtered_qs.count(), 1)
        self.assertEqual(filtered_qs.first(), self.event_today)

    def test_filter_empty_queryset(self):
        """Тест фильтрации пустого queryset."""
        qs = PrintEvent.objects.none()
        filter_data = {'document_name': 'test'}
        
        filtered_qs = PrintEventFilter(filter_data, queryset=qs).qs
        
        self.assertEqual(filtered_qs.count(), 0)
