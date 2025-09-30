from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView
from django.db.models import Count, Sum, Max, F
from django.db.models.functions import TruncDate, Coalesce
from .models import PrintEvent, Department, Printer, PrinterModel
from accounts.models import User  # Исправленный импорт
from .tables import PrintEventTable
from .filters import PrintEventFilter
from django.utils import timezone
from collections import OrderedDict
from datetime import datetime, timedelta
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views import View
from .importers import import_users_from_csv, import_print_events_from_json
from django.contrib.auth.decorators import login_required
import json
from django.conf import settings


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'printing/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика за последние 30 дней
        last_30_days = PrintEvent.objects.select_related('user', 'printer').filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=30)
        )
        
        context.update({
            'total_pages': last_30_days.aggregate(Sum('pages'))['pages__sum'] or 0,
            'total_documents': last_30_days.count(),
            'daily_stats': last_30_days.annotate(
                date=TruncDate('timestamp')
            ).values('date').annotate(
                pages=Sum('pages'),
                documents=Count('id')
            ).order_by('date'),
        })
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
        
        # Статистика по отделам (кэшируем агрегаты)
        department_cache_key = 'department_stats_top'
        department_stats = cache.get(department_cache_key)
        if department_stats is None:
            department_stats = Department.objects.prefetch_related("user_set").annotate(
                total_pages=Sum('users__print_events__pages'),
                total_documents=Count('users__print_events'),
                total_size=Sum('users__print_events__byte_size')
            ).order_by('-total_pages')
            cache.set(department_cache_key, department_stats, 300)

        # Статистика по пользователям (кэшируем топ-10)
        user_cache_key = 'user_stats_top10'
        user_stats = cache.get(user_cache_key)
        if user_stats is None:
            user_stats = User.objects.select_related('department').annotate(
                total_pages=Sum('print_events__pages'),
                total_documents=Count('print_events'),
                total_size=Sum('print_events__byte_size')
            ).order_by('-total_pages')[:10]
            cache.set(user_cache_key, list(user_stats), 300)

        context.update({
            'department_stats': department_stats,
            'user_stats': user_stats,
        })
        return context


@method_decorator(cache_page(60 * 5), name='dispatch')  # Кэширование на 5 минут
class PrintTreeView(TemplateView):
    template_name = 'printing/print_tree.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()
        query = PrintEvent.objects.select_related(
            'printer__department',
            'printer__model',
            'user'
        )
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                if settings.USE_TZ and timezone.is_naive(start_dt):
                    start_dt = timezone.make_aware(start_dt, timezone.get_default_timezone())
                query = query.filter(timestamp__gte=start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                if settings.USE_TZ and timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt, timezone.get_default_timezone())
                query = query.filter(timestamp__lte=end_dt)
            except ValueError:
                pass
        cache_key = f'print_tree_{start_date}_{end_date}'
        tree_data = cache.get(cache_key)
        if tree_data is None:
            results = query.values(
                'printer__department__code',
                'printer__department__name',
                'printer__model__code',
                'printer__room_number',
                'printer__printer_index',
                'user__fio',
                'document_name'
            ).annotate(
                page_sum=Sum('pages'),
                last_time=Max('timestamp')
            ).order_by('-page_sum')
            tree = {}
            total_pages = 0
            for row in results:
                dept_name = f"{row['printer__department__code']} — {row['printer__department__name']}"
                printer_name = (f"{row['printer__model__code']}-"
                              f"{row['printer__room_number']}-"
                              f"{row['printer__printer_index']}")
                user_name = row['user__fio']
                doc_name = row['document_name']
                pages = row['page_sum']
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
                    'timestamp': row['last_time']
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
        result = import_users_from_csv(file)
        return render(request, 'printing/import_users_result.html', {'result': result})


@method_decorator(csrf_exempt, name='dispatch')
class ImportPrintEventsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'printing/import_print_events_result.html', {'result': None})

    def post(self, request):
        import json
        events = None
        error = None
        # Если multipart/form-data — файл
        if 'file' in request.FILES:
            try:
                file = request.FILES['file']
                events = json.load(file)
            except Exception as e:
                error = f'Ошибка парсинга JSON-файла: {str(e)}'
        else:
            try:
                events = json.loads(request.body.decode('utf-8'))
            except Exception as e:
                error = f'Ошибка парсинга JSON: {str(e)}'
        if error:
            return render(request, 'printing/import_print_events_result.html', {'result': {'error': error}})
        if not isinstance(events, list):
            return render(request, 'printing/import_print_events_result.html', {'result': {'error': 'Неверный формат. Ожидается список событий'}})
        result = import_print_events_from_json(events)
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
