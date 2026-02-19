import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

from printing.models import Building, Computer, Department, Port, Printer, PrinterModel, PrintEvent

User = get_user_model()


class DepartmentFactory(factory.django.DjangoModelFactory):
    """Factory for Department model."""

    class Meta:
        model = Department

    code = factory.Sequence(lambda n: f"DEPT{n:03d}")
    name = factory.LazyAttribute(lambda obj: f"{obj.code} Department")


class BuildingFactory(factory.django.DjangoModelFactory):
    """Factory for Building model."""

    class Meta:
        model = Building

    code = factory.Sequence(lambda n: f"BLD{n:03d}")
    name = factory.LazyAttribute(lambda obj: f"{obj.code} Building")


class PrinterModelFactory(factory.django.DjangoModelFactory):
    """Factory for PrinterModel."""

    class Meta:
        model = PrinterModel

    code = factory.Sequence(lambda n: f"MODEL{n:03d}")
    manufacturer = factory.Faker("company")
    model = factory.Faker("word")
    is_color = factory.Faker("boolean")
    is_duplex = factory.Faker("boolean")


class PrinterFactory(factory.django.DjangoModelFactory):
    """Factory for Printer model."""

    class Meta:
        model = Printer

    name = factory.Sequence(lambda n: f"PRINTER-{n:03d}")
    model = factory.SubFactory(PrinterModelFactory)
    building = factory.SubFactory(BuildingFactory)
    department = factory.SubFactory(DepartmentFactory)
    room_number = factory.Sequence(lambda n: f"ROOM{n:03d}")
    printer_index = factory.Sequence(lambda n: n)
    cost_per_page = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    is_active = True


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n:03d}")
    fio = factory.Faker("name")
    department = factory.SubFactory(DepartmentFactory)
    is_active = True


class ComputerFactory(factory.django.DjangoModelFactory):
    """Factory for Computer model."""

    class Meta:
        model = Computer

    name = factory.Sequence(lambda n: f"PC{n:03d}")


class PortFactory(factory.django.DjangoModelFactory):
    """Factory for Port model."""

    class Meta:
        model = Port

    name = factory.Sequence(lambda n: f"PORT{n:03d}")


class PrintEventFactory(factory.django.DjangoModelFactory):
    """Factory for PrintEvent model."""

    class Meta:
        model = PrintEvent

    document_id = factory.Sequence(lambda n: n)
    document_name = factory.Faker("file_name", extension="pdf")
    user = factory.SubFactory(UserFactory)
    printer = factory.SubFactory(PrinterFactory)
    job_id = factory.Sequence(lambda n: f"job{n:06d}")
    timestamp = factory.LazyFunction(timezone.now)
    pages = factory.Faker("random_int", min=1, max=100)
    byte_size = factory.Faker("random_int", min=100, max=10000000)
    computer = factory.SubFactory(ComputerFactory)
    port = factory.SubFactory(PortFactory)
