import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from printing.models import Building, Computer, Department, Port, Printer, PrinterModel, PrintEvent
from tests.factories import PrinterFactory, UserFactory

User = get_user_model()


@pytest.fixture
def client() -> Client:
    """Django test client."""
    return Client()


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Temporary directory for file operations."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def department() -> Department:
    """Test department."""
    return Department.objects.create(code="IT", name="IT Department")


@pytest.fixture
def building() -> Building:
    """Test building."""
    return Building.objects.create(code="BLD1", name="Building 1")


@pytest.fixture
def printer_model() -> PrinterModel:
    """Test printer model."""
    return PrinterModel.objects.create(code="HP400", manufacturer="HP", model="LaserJet 400")


@pytest.fixture
def printer(department: Department, building: Building, printer_model: PrinterModel) -> Printer:
    """Test printer."""
    return Printer.objects.create(
        name="HP400-BLD1-IT-ROOM1-1",
        model=printer_model,
        building=building,
        department=department,
        room_number="ROOM1",
        printer_index=1,
        cost_per_page=2.00,
    )


@pytest.fixture
def user(department: Department) -> User:
    """Test user."""
    return User.objects.create_user(username="testuser", fio="Test User", department=department, password="testpass123")


@pytest.fixture
def print_event(user: User, printer: Printer) -> PrintEvent:
    """Test print event."""
    from django.utils import timezone

    return PrintEvent.objects.create(
        document_id=1,
        document_name="test.pdf",
        user=user,
        printer=printer,
        job_id="job123",
        timestamp=timezone.now(),
        pages=5,
        byte_size=1024,
    )


@pytest.fixture
def user_factory():
    """Factory fixture for creating users in pytest-style tests."""

    def factory(**kwargs):
        return UserFactory(**kwargs)

    return factory


@pytest.fixture
def printer_factory():
    """Factory fixture for creating printers in pytest-style tests."""

    def factory(**kwargs):
        return PrinterFactory(**kwargs)

    return factory


@pytest.fixture
def computer() -> Computer:
    """Test computer."""
    return Computer.objects.create(name="PC1")


@pytest.fixture
def port() -> Port:
    """Test port."""
    return Port.objects.create(name="USB001")


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass
