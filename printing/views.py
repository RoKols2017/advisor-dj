import json
from collections import OrderedDict
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Count, Max, Sum
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from accounts.models import User  # Исправленный импорт

from .filters import PrintEventFilter
from .services import import_print_events, import_users_from_csv_stream
from .models import Department, PrintEvent
from . import services as svc
from .tables import PrintEventTable


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'printing/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        stats = svc.get_dashboard_stats(days=30)
        context.update(stats)
        return context


class PrintEventsView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = PrintEvent
    table_class = PrintEventTable
    template_name = 'printing/print_events.html'
    filterset_class = PrintEventFilter
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Сумма страниц по отфильтрованным событиям
        total_pages = self.object_list.aggregate(total=Sum('pages'))['total'] or 0
        context['total_pages'] = total_pages
        return context


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'printing/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        data = svc.get_statistics_data(None, None)
        context.update({
            'department_stats': data['department_stats'],
            'user_stats': data['user_stats'],
        })
        return context


@method_decorator(cache_page(60 * 5), name='dispatch')  # Кэширование на 5 минут
class PrintTreeView(TemplateView):
    template_name = 'printing/print_tree.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()
        
        # Парсим даты из запроса
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                if settings.USE_TZ and timezone.is_naive(start_dt):
                    start_dt = timezone.make_aware(start_dt, timezone.get_default_timezone())
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                if settings.USE_TZ and timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt, timezone.get_default_timezone())
            except ValueError:
                pass
        
        cache_key = f'print_tree_{start_date}_{end_date}'
        tree_data = cache.get(cache_key)
        if tree_data is None:
            # Передаем реальные даты в сервис для фильтрации
            results = svc.get_statistics_data(start_date=start_dt, end_date=end_dt)['tree_results']
            tree = {}
            total_pages = 0
            for row in results:
                # Обработка None значений для безопасности
                dept_code = row.get('printer__department__code') or 'N/A'
                dept_name_val = row.get('printer__department__name') or 'Без отдела'
                dept_name = f"{dept_code} — {dept_name_val}"
                
                model_code = row.get('printer__model__code') or 'N/A'
                room = row.get('printer__room_number') or 'N/A'
                index = row.get('printer__printer_index') or 'N/A'
                printer_name = f"{model_code}-{room}-{index}"
                
                user_name = row.get('user__fio') or 'Неизвестный'
                doc_name = row.get('document_name') or 'Без названия'
                pages = row.get('page_sum') or 0
                total_pages += pages
                dept = tree.setdefault(dept_name, {
                    'total': 0,
                    'printers': OrderedDict()
                })
                dept['total'] += pages
                printer = dept['printers'].setdefault(printer_name, {
                    'total': 0,
                    'users': OrderedDict()
                })
                printer['total'] += pages
                user = printer['users'].setdefault(user_name, {
                    'total': 0,
                    'docs': OrderedDict()
                })
                user['total'] += pages
                doc_entry = user['docs'].setdefault(doc_name, [])
                doc_entry.append({
                    'pages': pages,
                    'timestamp': row.get('last_time')
                })
            # Сортировка и проценты
            sorted_tree = OrderedDict()
            for dept_name, dept_data in sorted(
                tree.items(), key=lambda x: x[1]['total'], reverse=True
            ):
                dept_percent = (dept_data['total'] * 100 / total_pages) if total_pages else 0
                sorted_printers = OrderedDict()
                for printer_name, printer_data in sorted(
                    dept_data['printers'].items(), key=lambda x: x[1]['total'], reverse=True
                ):
                    printer_percent = (printer_data['total'] * 100 / dept_data['total']) if dept_data['total'] else 0
                    sorted_users = OrderedDict()
                    for user_name, user_data in sorted(
                        printer_data['users'].items(), key=lambda x: x[1]['total'], reverse=True
                    ):
                        user_percent = (user_data['total'] * 100 / printer_data['total']) if printer_data['total'] else 0
                        sorted_docs = OrderedDict()
                        for doc_name, doc_entries in sorted(
                            user_data['docs'].items(),
                            key=lambda x: sum(entry['pages'] for entry in x[1]),
                            reverse=True
                        ):
                            if len(doc_name) > 80:
                                doc_name = f"{doc_name[:79]}…"
                            sorted_docs[doc_name] = doc_entries
                        user_data['docs'] = sorted_docs
                        user_data['percent'] = round(user_percent, 1)
                        sorted_users[user_name] = user_data
                    printer_data['users'] = sorted_users
                    printer_data['percent'] = round(printer_percent, 1)
                    sorted_printers[printer_name] = printer_data
                dept_data['printers'] = sorted_printers
                dept_data['percent'] = round(dept_percent, 1)
                sorted_tree[dept_name] = dept_data
            tree_data = {
                'tree': sorted_tree,
                'total_pages': total_pages
            }
            cache.set(cache_key, tree_data, 300)
        context.update(tree_data)
        context.update({
            'start_date': start_date,
            'end_date': end_date
        })
        return context


class ImportUsersView(LoginRequiredMixin, View):
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 МБ максимальный размер файла
    
    def get(self, request):
        return render(request, 'printing/import_users_result.html', {'result': None})

    def post(self, request):
        if 'file' not in request.FILES:
            return render(request, 'printing/import_users_result.html', {
                'result': {'error': 'Файл не найден'}
            })
        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            return render(request, 'printing/import_users_result.html', {
                'result': {'error': 'Неверный формат файла. Ожидается CSV'}
            })
        # Проверка размера файла
        if file.size > self.MAX_FILE_SIZE:
            return render(request, 'printing/import_users_result.html', {
                'result': {'error': f'Размер файла превышает допустимый лимит ({self.MAX_FILE_SIZE / 1024 / 1024:.1f} МБ)'}
            })
        result = import_users_from_csv_stream(file)
        return render(request, 'printing/import_users_result.html', {'result': result})


class ImportPrintEventsView(LoginRequiredMixin, View):
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ максимальный размер файла для JSON событий
    
    def get(self, request):
        return render(request, 'printing/import_print_events_result.html', {'result': None})

    def post(self, request):
        events = None
        error = None
        # Если multipart/form-data — файл
        if 'file' in request.FILES:
            try:
                file = request.FILES['file']
                # Проверка размера файла
                if file.size > self.MAX_FILE_SIZE:
                    error = f'Размер файла превышает допустимый лимит ({self.MAX_FILE_SIZE / 1024 / 1024:.1f} МБ)'
                else:
                    events = json.load(file)
            except json.JSONDecodeError as e:
                error = f'Ошибка парсинга JSON-файла: {str(e)}'
            except (ValueError, TypeError) as e:
                error = f'Ошибка обработки файла: {str(e)}'
            except Exception as e:
                error = f'Неожиданная ошибка при обработке файла: {str(e)}'
        else:
            # Проверка размера тела запроса
            body_size = len(request.body)
            if body_size > self.MAX_FILE_SIZE:
                error = f'Размер данных превышает допустимый лимит ({self.MAX_FILE_SIZE / 1024 / 1024:.1f} МБ)'
            else:
                try:
                    events = json.loads(request.body.decode('utf-8'))
                except json.JSONDecodeError as e:
                    error = f'Ошибка парсинга JSON: {str(e)}'
                except (UnicodeDecodeError, ValueError, TypeError) as e:
                    error = f'Ошибка декодирования данных: {str(e)}'
                except Exception as e:
                    error = f'Неожиданная ошибка при обработке данных: {str(e)}'
        if error:
            return render(request, 'printing/import_print_events_result.html', {'result': {'error': error}})
        if not isinstance(events, list):
            return render(request, 'printing/import_print_events_result.html', {'result': {'error': 'Неверный формат. Ожидается список событий'}})
        result = import_print_events(events)
        return render(request, 'printing/import_print_events_result.html', {'result': result})


class PrintEventListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка событий печати.

    Attributes:
        model (Model): Модель PrintEvent
        template_name (str): Путь к шаблону
        context_object_name (str): Имя переменной контекста
        paginate_by (int): Количество элементов на странице

    Methods:
        get_queryset(): Возвращает отфильтрованный QuerySet
        get_context_data(): Добавляет дополнительные данные в контекст

    Example:
        URL Configuration:
        path('events/', PrintEventListView.as_view(), name='event_list')
    """
    model = PrintEvent
    template_name = 'printing/event_list.html'
    context_object_name = 'events'
    paginate_by = 50

    def get_queryset(self):
        """
        Возвращает QuerySet с предзагруженными связанными объектами.

        Returns:
            QuerySet: Отфильтрованный и отсортированный список событий
        """
        return PrintEvent.objects.select_related(
            'user',
            'printer'
        ).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        """
        Добавляет статистику в контекст.

        Returns:
            dict: Расширенный контекст шаблона
        """
        context = super().get_context_data(**kwargs)
        context['total_pages'] = self.get_queryset().aggregate(
            total=Sum('pages')
        )['total']
        return context


@login_required
def statistics_view(request):
    """
    Представление для отображения статистики печати.

    Args:
        request (HttpRequest): HTTP запрос

    Returns:
        HttpResponse: Ответ с отрендеренным шаблоном статистики

    Example:
        URL Configuration:
        path('statistics/', statistics_view, name='statistics')
    """
    context = {
        'total_events': PrintEvent.objects.count(),
        'total_pages': PrintEvent.objects.aggregate(
            total=Sum('pages')
        )['total'],
        'department_stats': Department.objects.annotate(
            event_count=Count('user__printevent'),
            page_count=Sum('user__printevent__pages')
        )
    }
    return render(request, 'printing/statistics.html', context)


class UserInfoView(LoginRequiredMixin, TemplateView):
    template_name = 'user_info.html'
