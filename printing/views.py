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


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'printing/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика за последние 30 дней
        last_30_days = PrintEvent.objects.filter(
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


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'printing/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика по отделам
        department_stats = Department.objects.annotate(
            total_pages=Sum('users__print_events__pages'),
            total_documents=Count('users__print_events'),
            total_size=Sum('users__print_events__byte_size')
        ).order_by('-total_pages')

        # Статистика по пользователям
        user_stats = User.objects.annotate(
            total_pages=Sum('print_events__pages'),
            total_documents=Count('print_events'),
            total_size=Sum('print_events__byte_size')
        ).order_by('-total_pages')[:10]

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
        
        # Получаем параметры фильтрации
        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()

        # Базовый запрос с оптимизацией через select_related
        query = PrintEvent.objects.select_related(
            'printer__department',
            'printer__model',
            'user'
        )

        # Применяем фильтры по датам
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(timestamp__gte=start_dt)
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(timestamp__lte=end_dt)
            except ValueError:
                pass

        # Кэш-ключ на основе параметров фильтрации
        cache_key = f'print_tree_{start_date}_{end_date}'
        tree_data = cache.get(cache_key)

        if tree_data is None:
            # Агрегируем данные с группировкой
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

            # Строим дерево
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

                # Обновляем общую статистику
                total_pages += pages

                # Строим дерево с автоматическим созданием уровней
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

                # Добавляем информацию о документе
                doc_entry = user['docs'].setdefault(doc_name, [])
                doc_entry.append({
                    'pages': pages,
                    'timestamp': row['last_time']
                })

            # Сортируем все уровни по количеству страниц
            sorted_tree = OrderedDict()
            for dept_name, dept_data in sorted(
                tree.items(),
                key=lambda x: x[1]['total'],
                reverse=True
            ):
                sorted_printers = OrderedDict()
                for printer_name, printer_data in sorted(
                    dept_data['printers'].items(),
                    key=lambda x: x[1]['total'],
                    reverse=True
                ):
                    sorted_users = OrderedDict()
                    for user_name, user_data in sorted(
                        printer_data['users'].items(),
                        key=lambda x: x[1]['total'],
                        reverse=True
                    ):
                        # Сортируем документы по количеству страниц
                        sorted_docs = OrderedDict()
                        for doc_name, doc_entries in sorted(
                            user_data['docs'].items(),
                            key=lambda x: sum(entry['pages'] for entry in x[1]),
                            reverse=True
                        ):
                            # Обрезаем длинные имена документов
                            if len(doc_name) > 80:
                                doc_name = f"{doc_name[:79]}…"
                            sorted_docs[doc_name] = doc_entries

                        user_data['docs'] = sorted_docs
                        sorted_users[user_name] = user_data

                    printer_data['users'] = sorted_users
                    sorted_printers[printer_name] = printer_data

                dept_data['printers'] = sorted_printers
                sorted_tree[dept_name] = dept_data

            tree_data = {
                'tree': sorted_tree,
                'total_pages': total_pages
            }
            
            # Сохраняем в кэш на 5 минут
            cache.set(cache_key, tree_data, 300)

        context.update(tree_data)
        context.update({
            'start_date': start_date,
            'end_date': end_date
        })
        
        return context


class ImportUsersView(LoginRequiredMixin, View):
    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Файл не найден'}, status=400)
            
        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            return JsonResponse({'error': 'Неверный формат файла. Ожидается CSV'}, status=400)
            
        result = import_users_from_csv(file)
        return JsonResponse(result)


@method_decorator(csrf_exempt, name='dispatch')
class ImportPrintEventsView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            events = request.json()
            if not isinstance(events, list):
                return JsonResponse({'error': 'Неверный формат. Ожидается список событий'}, status=400)
                
            result = import_print_events_from_json(events)
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


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
