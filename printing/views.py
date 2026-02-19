import hmac
import json
from collections import OrderedDict
from datetime import date, datetime, time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Count, Sum
from django.http import HttpResponseForbidden, QueryDict
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from . import services as svc
from .filters import PrintEventFilter
from .models import Department, PrintEvent
from .services import import_print_events, import_users_from_csv_stream
from .tables import PrintEventTable


def _has_valid_import_token(request) -> bool:
    expected_token = (getattr(settings, "IMPORT_TOKEN", "") or "").strip()
    if not expected_token:
        return False

    provided_token = (
        request.headers.get("X-Import-Token")
        or request.META.get("HTTP_X_IMPORT_TOKEN")
        or request.POST.get("import_token", "")
    ).strip()

    return bool(provided_token) and hmac.compare_digest(provided_token, expected_token)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "printing/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stats = svc.get_dashboard_stats(days=30)
        context.update(stats)
        return context


class PrintEventsView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = PrintEvent
    table_class = PrintEventTable
    template_name = "printing/print_events.html"
    filterset_class = PrintEventFilter
    paginate_by = 50

    def get(self, request, *args, **kwargs):
        """Перехватываем GET-запрос для установки дат по умолчанию."""
        # Проверяем наличие параметров дат (DateFromToRangeFilter использует timestamp_min и timestamp_max)
        timestamp_min = request.GET.get("timestamp_min", "").strip()
        timestamp_max = request.GET.get("timestamp_max", "").strip()

        # Если оба параметра отсутствуют, делаем редирект с датами по умолчанию
        if not timestamp_min and not timestamp_max:
            today = date.today()
            default_start = date(today.year, today.month, 1)
            default_end = today

            q = QueryDict(mutable=True)
            q.update(request.GET)
            q["timestamp_min"] = default_start.strftime("%Y-%m-%d")
            q["timestamp_max"] = default_end.strftime("%Y-%m-%d")
            return redirect(f"{request.path}?{q.urlencode()}")

        # Если указан только один параметр, добавляем второй
        if not timestamp_min or not timestamp_max:
            q = QueryDict(mutable=True)
            q.update(request.GET)
            today = date.today()
            if not timestamp_min:
                default_start = date(today.year, today.month, 1)
                q["timestamp_min"] = default_start.strftime("%Y-%m-%d")
            if not timestamp_max:
                q["timestamp_max"] = today.strftime("%Y-%m-%d")
            return redirect(f"{request.path}?{q.urlencode()}")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Сумма страниц по отфильтрованным событиям
        total_pages = self.object_list.aggregate(total=Sum("pages"))["total"] or 0
        context["total_pages"] = total_pages
        return context


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = "printing/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date_str = self.request.GET.get("start_date", "").strip()
        end_date_str = self.request.GET.get("end_date", "").strip()

        # Если даты не указаны, устанавливаем по умолчанию:
        # с первого числа текущего месяца до сегодня
        if not start_date_str or not end_date_str:
            today = date.today()
            default_start = date(today.year, today.month, 1)
            default_end = today

            if not start_date_str:
                start_date_str = default_start.strftime("%Y-%m-%d")
            if not end_date_str:
                end_date_str = default_end.strftime("%Y-%m-%d")

        # Парсим даты из запроса
        start_dt = None
        end_dt = None
        if start_date_str:
            try:
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                if settings.USE_TZ and timezone.is_naive(start_dt):
                    start_dt = timezone.make_aware(start_dt, timezone.get_default_timezone())
            except ValueError:
                pass
        if end_date_str:
            try:
                end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                if settings.USE_TZ and timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt, timezone.get_default_timezone())
            except ValueError:
                pass

        # Если после парсинга даты все еще None (ошибка парсинга),
        # используем значения по умолчанию
        if start_dt is None or end_dt is None:
            today = timezone.now().date()
            default_start = date(today.year, today.month, 1)
            default_end = today
            start_dt = timezone.make_aware(datetime.combine(default_start, time.min))
            end_dt = timezone.make_aware(datetime.combine(default_end, time.max))
            start_date_str = default_start.strftime("%Y-%m-%d")
            end_date_str = default_end.strftime("%Y-%m-%d")

        data = svc.get_statistics_data(start_date=start_dt, end_date=end_dt)
        context.update(
            {
                "department_stats": data["department_stats"],
                "user_stats": data["user_stats"],
                "start_date": start_date_str,
                "end_date": end_date_str,
            }
        )
        return context


@method_decorator(cache_page(60 * 5), name="dispatch")  # Кэширование на 5 минут
class PrintTreeView(LoginRequiredMixin, TemplateView):
    template_name = "printing/print_tree.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date_str = self.request.GET.get("start_date", "").strip()
        end_date_str = self.request.GET.get("end_date", "").strip()

        # Если даты не указаны, устанавливаем по умолчанию:
        # с первого числа текущего месяца до сегодня
        if not start_date_str or not end_date_str:
            today = date.today()
            default_start = date(today.year, today.month, 1)
            default_end = today

            if not start_date_str:
                start_date_str = default_start.strftime("%Y-%m-%d")
            if not end_date_str:
                end_date_str = default_end.strftime("%Y-%m-%d")

        # Парсим даты из запроса
        start_dt = None
        end_dt = None
        if start_date_str:
            try:
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                if settings.USE_TZ and timezone.is_naive(start_dt):
                    start_dt = timezone.make_aware(start_dt, timezone.get_default_timezone())
            except ValueError:
                pass
        if end_date_str:
            try:
                end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                if settings.USE_TZ and timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt, timezone.get_default_timezone())
            except ValueError:
                pass

        # Если после парсинга даты все еще None (ошибка парсинга),
        # используем значения по умолчанию
        if start_dt is None or end_dt is None:
            today = timezone.now().date()
            default_start = date(today.year, today.month, 1)
            default_end = today
            start_dt = timezone.make_aware(datetime.combine(default_start, time.min))
            end_dt = timezone.make_aware(datetime.combine(default_end, time.max))
            start_date_str = default_start.strftime("%Y-%m-%d")
            end_date_str = default_end.strftime("%Y-%m-%d")

        cache_key = f"print_tree_{start_date_str}_{end_date_str}"
        tree_data = cache.get(cache_key)
        if tree_data is None:
            # Передаем реальные даты в сервис для фильтрации
            results = svc.get_statistics_data(start_date=start_dt, end_date=end_dt)["tree_results"]
            tree = {}
            total_pages = 0
            for row in results:
                # Обработка None значений для безопасности
                dept_name_val = row.get("printer__department__name") or "Без отдела"
                dept_name = dept_name_val

                model_code = row.get("printer__model__code") or "N/A"
                room = row.get("printer__room_number") or "N/A"
                index = row.get("printer__printer_index") or "N/A"
                printer_name = f"{model_code}-{room}-{index}"

                user_name = row.get("user__fio") or "Неизвестный"
                doc_name = row.get("document_name") or "Без названия"
                pages = row.get("page_sum") or 0
                total_pages += pages
                dept = tree.setdefault(dept_name, {"total": 0, "printers": OrderedDict()})
                dept["total"] += pages
                printer = dept["printers"].setdefault(printer_name, {"total": 0, "users": OrderedDict()})
                printer["total"] += pages
                user = printer["users"].setdefault(user_name, {"total": 0, "docs": OrderedDict()})
                user["total"] += pages
                doc_entry = user["docs"].setdefault(doc_name, [])
                doc_entry.append({"pages": pages, "timestamp": row.get("last_time")})
            # Сортировка и проценты
            sorted_tree = OrderedDict()
            for dept_name, dept_data in sorted(tree.items(), key=lambda x: x[1]["total"], reverse=True):
                dept_percent = (dept_data["total"] * 100 / total_pages) if total_pages else 0
                sorted_printers = OrderedDict()
                for printer_name, printer_data in sorted(
                    dept_data["printers"].items(), key=lambda x: x[1]["total"], reverse=True
                ):
                    printer_percent = (printer_data["total"] * 100 / dept_data["total"]) if dept_data["total"] else 0
                    sorted_users = OrderedDict()
                    for user_name, user_data in sorted(
                        printer_data["users"].items(), key=lambda x: x[1]["total"], reverse=True
                    ):
                        user_percent = (
                            (user_data["total"] * 100 / printer_data["total"]) if printer_data["total"] else 0
                        )
                        sorted_docs = OrderedDict()
                        for doc_name, doc_entries in sorted(
                            user_data["docs"].items(), key=lambda x: sum(entry["pages"] for entry in x[1]), reverse=True
                        ):
                            if len(doc_name) > 80:
                                doc_name = f"{doc_name[:79]}…"
                            sorted_docs[doc_name] = doc_entries
                        user_data["docs"] = sorted_docs
                        user_data["percent"] = round(user_percent, 1)
                        sorted_users[user_name] = user_data
                    printer_data["users"] = sorted_users
                    printer_data["percent"] = round(printer_percent, 1)
                    sorted_printers[printer_name] = printer_data
                dept_data["printers"] = sorted_printers
                dept_data["percent"] = round(dept_percent, 1)
                sorted_tree[dept_name] = dept_data
            tree_data = {"tree": sorted_tree, "total_pages": total_pages}
            # Для периодов, которые уже закончились, кэшируем дольше
            cache_timeout = 300  # 5 минут по умолчанию
            if end_dt and end_dt.date() < date.today():
                cache_timeout = 3600 * 24  # 24 часа для прошлых периодов
            cache.set(cache_key, tree_data, cache_timeout)
        context.update(tree_data)
        context.update({"start_date": start_date_str, "end_date": end_date_str})
        return context


class ImportUsersView(LoginRequiredMixin, View):
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 МБ максимальный размер файла

    def get(self, request):
        return render(request, "printing/import_users_result.html", {"result": None})

    def post(self, request):
        if not _has_valid_import_token(request):
            return HttpResponseForbidden("Invalid or missing import token")

        if "file" not in request.FILES:
            return render(request, "printing/import_users_result.html", {"result": {"error": "Файл не найден"}})
        file = request.FILES["file"]
        if not file.name.endswith(".csv"):
            return render(
                request,
                "printing/import_users_result.html",
                {"result": {"error": "Неверный формат файла. Ожидается CSV"}},
            )
        # Проверка размера файла
        if file.size > self.MAX_FILE_SIZE:
            return render(
                request,
                "printing/import_users_result.html",
                {
                    "result": {
                        "error": f"Размер файла превышает допустимый лимит ({self.MAX_FILE_SIZE / 1024 / 1024:.1f} МБ)"
                    }
                },
            )
        result = import_users_from_csv_stream(file)
        return render(request, "printing/import_users_result.html", {"result": result})


class ImportPrintEventsView(LoginRequiredMixin, View):
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ максимальный размер файла для JSON событий

    def get(self, request):
        return render(request, "printing/import_print_events_result.html", {"result": None})

    def post(self, request):
        if not _has_valid_import_token(request):
            return HttpResponseForbidden("Invalid or missing import token")

        events = None
        error = None
        # Если multipart/form-data — файл
        if "file" in request.FILES:
            try:
                file = request.FILES["file"]
                # Проверка размера файла
                if file.size > self.MAX_FILE_SIZE:
                    error = f"Размер файла превышает допустимый лимит ({self.MAX_FILE_SIZE / 1024 / 1024:.1f} МБ)"
                else:
                    events = json.load(file)
            except json.JSONDecodeError as e:
                error = f"Ошибка парсинга JSON-файла: {str(e)}"
            except (ValueError, TypeError) as e:
                error = f"Ошибка обработки файла: {str(e)}"
            except Exception as e:
                error = f"Неожиданная ошибка при обработке файла: {str(e)}"
        else:
            # Проверка размера тела запроса
            body_size = len(request.body)
            if body_size > self.MAX_FILE_SIZE:
                error = f"Размер данных превышает допустимый лимит ({self.MAX_FILE_SIZE / 1024 / 1024:.1f} МБ)"
            else:
                try:
                    events = json.loads(request.body.decode("utf-8"))
                except json.JSONDecodeError as e:
                    error = f"Ошибка парсинга JSON: {str(e)}"
                except (UnicodeDecodeError, ValueError, TypeError) as e:
                    error = f"Ошибка декодирования данных: {str(e)}"
                except Exception as e:
                    error = f"Неожиданная ошибка при обработке данных: {str(e)}"
        if error:
            return render(request, "printing/import_print_events_result.html", {"result": {"error": error}})
        if not isinstance(events, list):
            return render(
                request,
                "printing/import_print_events_result.html",
                {"result": {"error": "Неверный формат. Ожидается список событий"}},
            )
        result = import_print_events(events)
        return render(request, "printing/import_print_events_result.html", {"result": result})


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
    template_name = "printing/event_list.html"
    context_object_name = "events"
    paginate_by = 50

    def get_queryset(self):
        """
        Возвращает QuerySet с предзагруженными связанными объектами.

        Returns:
            QuerySet: Отфильтрованный и отсортированный список событий
        """
        return PrintEvent.objects.select_related("user", "printer").order_by("-timestamp")

    def get_context_data(self, **kwargs):
        """
        Добавляет статистику в контекст.

        Returns:
            dict: Расширенный контекст шаблона
        """
        context = super().get_context_data(**kwargs)
        context["total_pages"] = self.get_queryset().aggregate(total=Sum("pages"))["total"]
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
        "total_events": PrintEvent.objects.count(),
        "total_pages": PrintEvent.objects.aggregate(total=Sum("pages"))["total"],
        "department_stats": Department.objects.annotate(
            event_count=Count("users__print_events", distinct=True), page_count=Sum("users__print_events__pages")
        ),
    }
    return render(request, "printing/statistics.html", context)


class UserInfoView(LoginRequiredMixin, TemplateView):
    template_name = "user_info.html"
