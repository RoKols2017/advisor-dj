from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Building, Computer, Department, Port, Printer, PrinterModel, PrintEvent
from .resources import (
    BuildingResource,
    ComputerResource,
    DepartmentResource,
    PortResource,
    PrinterModelResource,
    PrinterResource,
    PrintEventResource,
)


@admin.register(Building)
class BuildingAdmin(ImportExportModelAdmin):
    resource_class = BuildingResource
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name")
    ordering = ("name",)


@admin.register(PrinterModel)
class PrinterModelAdmin(ImportExportModelAdmin):
    resource_class = PrinterModelResource
    list_display = ("code", "manufacturer", "model", "is_color", "is_duplex", "created_at")
    list_filter = ("is_color", "is_duplex", "manufacturer")
    search_fields = ("code", "manufacturer", "model")
    ordering = ("manufacturer", "model")


@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    resource_class = DepartmentResource
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Computer)
class ComputerAdmin(ImportExportModelAdmin):
    resource_class = ComputerResource
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Port)
class PortAdmin(ImportExportModelAdmin):
    resource_class = PortResource
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Printer)
class PrinterAdmin(ImportExportModelAdmin):
    resource_class = PrinterResource
    list_display = ("name", "model", "building", "created_at")
    list_filter = ("model", "building")
    search_fields = ("name", "model__model", "building__name")
    ordering = ("name",)


@admin.register(PrintEvent)
class PrintEventAdmin(ImportExportModelAdmin):
    resource_class = PrintEventResource
    list_display = ("document_name", "user", "printer", "timestamp", "pages", "byte_size")
    list_filter = ("printer", "timestamp", "computer")
    search_fields = ("document_name", "user__username", "printer__name", "computer__name")
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"
    raw_id_fields = ("user", "printer", "computer", "port")
