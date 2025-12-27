import django_filters
from django import forms

from .models import Computer, Department, Printer, PrintEvent


class PrintEventFilter(django_filters.FilterSet):
    timestamp = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'class': 'form-control', 'type': 'date'})
    )
    document_name = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    user__department = django_filters.ModelChoiceFilter(
        queryset=Department.objects.all().order_by('name'),
        label='Отдел',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    printer = django_filters.ModelChoiceFilter(
        queryset=Printer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    computer = django_filters.ModelChoiceFilter(
        queryset=Computer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Переопределяем поле для отображения только названия отдела
        if 'user__department' in self.form.fields:
            field = self.form.fields['user__department']
            # Переопределяем метод label_from_instance для отображения только названия
            def label_from_instance(obj):
                return obj.name
            
            field.label_from_instance = label_from_instance

    class Meta:
        model = PrintEvent
        fields = ['timestamp', 'document_name', 'user__department', 'printer', 'computer'] 