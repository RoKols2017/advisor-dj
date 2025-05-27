import django_tables2 as tables
from .models import PrintEvent


class PrintEventTable(tables.Table):
    user = tables.Column(linkify=True)
    printer = tables.Column(linkify=True)
    computer = tables.Column(linkify=True)
    byte_size = tables.Column(verbose_name='Размер')
    pages = tables.Column(verbose_name='Страниц')

    def render_byte_size(self, value):
        if value < 1024:
            return f"{value} B"
        elif value < 1024 * 1024:
            return f"{value/1024:.1f} KB"
        else:
            return f"{value/(1024*1024):.1f} MB"

    class Meta:
        model = PrintEvent
        template_name = "django_tables2/bootstrap5.html"
        fields = ('timestamp', 'document_name', 'user', 'printer', 'computer', 'pages', 'byte_size')
        attrs = {"class": "table table-striped table-hover"}
        order_by = '-timestamp' 