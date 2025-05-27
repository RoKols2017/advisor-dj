from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Building, PrinterModel, Department, Computer, Port, Printer, PrintEvent
from accounts.models import User


class BuildingResource(resources.ModelResource):
    class Meta:
        model = Building
        import_id_fields = ['code']
        fields = ('code', 'name')


class PrinterModelResource(resources.ModelResource):
    class Meta:
        model = PrinterModel
        import_id_fields = ['code']
        fields = ('code', 'manufacturer', 'model', 'is_color', 'is_duplex')


class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        import_id_fields = ['name']
        fields = ('name',)


class ComputerResource(resources.ModelResource):
    class Meta:
        model = Computer
        import_id_fields = ['name']
        fields = ('name',)


class PortResource(resources.ModelResource):
    class Meta:
        model = Port
        import_id_fields = ['name']
        fields = ('name',)


class PrinterResource(resources.ModelResource):
    model = fields.Field(
        column_name='model',
        attribute='model',
        widget=ForeignKeyWidget(PrinterModel, 'code')
    )
    building = fields.Field(
        column_name='building',
        attribute='building',
        widget=ForeignKeyWidget(Building, 'code')
    )

    class Meta:
        model = Printer
        import_id_fields = ['name']
        fields = ('name', 'model', 'building')


class PrintEventResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )
    printer = fields.Field(
        column_name='printer',
        attribute='printer',
        widget=ForeignKeyWidget(Printer, 'name')
    )
    computer = fields.Field(
        column_name='computer',
        attribute='computer',
        widget=ForeignKeyWidget(Computer, 'name')
    )
    port = fields.Field(
        column_name='port',
        attribute='port',
        widget=ForeignKeyWidget(Port, 'name')
    )

    class Meta:
        model = PrintEvent
        fields = (
            'document_id', 'document_name', 'user', 'printer',
            'job_id', 'timestamp', 'byte_size', 'pages',
            'computer', 'port'
        )
        export_order = fields 