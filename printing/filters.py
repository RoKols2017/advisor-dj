import django_filters
from django import forms
from .models import PrintEvent, Department, Printer, Computer


class PrintEventFilter(django_filters.FilterSet):
    timestamp = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={'class': 'form-control', 'type': 'date'})
    )
    document_name = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    user__department = django_filters.ModelChoiceFilter(
        queryset=Department.objects.all(),
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

    class Meta:
        model = PrintEvent
        fields = ['timestamp', 'document_name', 'user__department', 'printer', 'computer'] 