from __future__ import annotations

import csv
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Sum, Count, Max
from django.db.models.functions import TruncDate

from accounts.models import User

from .models import (
    Building,
    Computer,
    Department,
    Port,
    Printer,
    PrinterModel,
    PrintEvent,
)

logger = logging.getLogger(__name__)


def _get_or_create_ci_department(code: str) -> Department:
    normalized = (code or "").strip().lower()
    if not normalized:
        raise ValueError("Department code is empty")
    existing = Department.objects.filter(code__iexact=normalized).first()
    if existing:
        return existing
    return Department.objects.create(code=normalized, name=normalized.upper())


def _get_or_create_ci_building(code: str) -> Building:
    normalized = (code or "").strip().lower()
    if not normalized:
        raise ValueError("Building code is empty")
    existing = Building.objects.filter(code__iexact=normalized).first()
    if existing:
        return existing
    return Building.objects.create(code=normalized, name=normalized.upper())


def _get_or_create_ci_printer_model(model_code: str) -> PrinterModel:
    normalized = (model_code or "").strip()
    if not normalized:
        raise ValueError("Printer model code is empty")
    existing = PrinterModel.objects.filter(code__iexact=normalized).first()
    if existing:
        return existing
    # Парсим код модели: ожидается формат "Manufacturer Model" или просто код
    parts = normalized.split(maxsplit=1)
    manufacturer = parts[0] if parts else normalized
    model = parts[1] if len(parts) > 1 else ""
    return PrinterModel.objects.create(code=normalized, manufacturer=manufacturer, model=model)


def _get_or_create_ci_printer(
    building: Building,
    room_number: str,
    printer_index: int,
    printer_model: PrinterModel,
    department: Department,
    full_name: str,
) -> Printer:
    existing = (
        Printer.objects.filter(
            building=building,
            room_number__iexact=(room_number or "").strip(),
            printer_index=printer_index,
        )
        .select_related("building", "model", "department")
        .first()
    )
    if existing:
        return existing
    return Printer.objects.create(
        name=full_name,
        model=printer_model,
        department=department,
        building=building,
        room_number=(room_number or "").strip(),
        printer_index=printer_index,
        is_active=True,
    )


@dataclass
class ImportUsersResult:
    created: int
    errors: list[str]


def import_users_from_csv_stream(file_bytes) -> dict[str, Any]:
    created = 0
    errors: list[str] = []
    try:
        decoded = file_bytes.read().decode("utf-8-sig")
        reader = csv.DictReader(decoded.splitlines())
        with transaction.atomic():
            for row in reader:
                try:
                    username = (row.get("SamAccountName") or "").strip().lower()
                    fio = (row.get("DisplayName") or "").strip()
                    dept_code = (row.get("OU") or "").strip().lower()
                    if not username or not dept_code:
                        continue
                    department = _get_or_create_ci_department(dept_code)
                    user, was_created = User.objects.update_or_create(
                        username=username,
                        defaults={
                            "fio": fio or username,
                            "department": department,
                            "is_active": True,
                        },
                    )
                    if was_created:
                        created += 1
                except (ValueError, TypeError, KeyError) as e:
                    # Обрабатываем ожидаемые ошибки валидации отдельно
                    msg = f"Row validation error (line {reader.line_num}): {e}"
                    logger.warning(msg, exc_info=True)
                    errors.append(msg)
                except Exception as e:  # noqa: BLE001 - логируем и продолжаем пакет
                    msg = f"Row processing error (line {reader.line_num}): {e}"
                    logger.error(msg, exc_info=True)
                    errors.append(msg)
    except (UnicodeDecodeError, csv.Error) as e:
        # Обрабатываем ошибки чтения файла отдельно
        msg = f"File reading error: {e}"
        logger.error(msg, exc_info=True)
        errors.append(msg)
    except Exception as e:  # noqa: BLE001
        msg = f"Users import failed: {e}"
        logger.error(msg, exc_info=True)
        errors.append(msg)
    return {"created": created, "errors": errors}


def import_print_events(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    created = 0
    errors: list[str] = []
    BATCH_SIZE = 100  # Обрабатываем события батчами для оптимизации транзакций
    
    events_list = list(events) if not isinstance(events, list) else events
    total_events = len(events_list)
    
    # Получаем все существующие job_id одним запросом для дедупликации
    existing_job_ids = set(
        PrintEvent.objects.filter(
            job_id__in=[e.get("JobID") or "UNKNOWN" for e in events_list if e.get("JobID")]
        ).values_list("job_id", flat=True)
    )
    
    # Обрабатываем события батчами
    for batch_start in range(0, total_events, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_events)
        batch_events = events_list[batch_start:batch_end]
        
        with transaction.atomic():
            batch_created = 0
            for event in batch_events:
                try:
                    username = (event.get("Param3") or "").strip().lower()
                    document_name = event.get("Param2", "")
                    document_id = int(event.get("Param1") or 0)
                    byte_size = int(event.get("Param7") or 0)
                    pages = int(event.get("Param8") or 0)
                    timestamp_ms = int(str(event.get("TimeCreated", "0")).replace("/Date(", "").replace(")/", ""))
                    ts = timezone.datetime.fromtimestamp(timestamp_ms / 1000)
                    if timezone.is_naive(ts):
                        ts = timezone.make_aware(ts, timezone.get_default_timezone())
                    job_id = event.get("JobID") or "UNKNOWN"

                    # Проверка на дубликаты через предзагруженный set
                    if job_id in existing_job_ids:
                        continue
                    existing_job_ids.add(job_id)  # Добавляем в set для проверки в рамках батча

                    printer_name_raw = (event.get("Param5") or "").strip().lower()
                    parts = printer_name_raw.split("-")
                    if len(parts) != 5:
                        errors.append(f"Invalid printer format: {printer_name_raw}")
                        continue
                    model_code, bld_code, dept_code, room_number, printer_index_str = parts
                    try:
                        printer_index = int(printer_index_str)
                    except ValueError:
                        errors.append(f"Invalid printer index: {printer_index_str}")
                        continue

                    building = _get_or_create_ci_building(bld_code)
                    department = _get_or_create_ci_department(dept_code)
                    printer_model = _get_or_create_ci_printer_model(model_code)
                    printer = _get_or_create_ci_printer(
                        building=building,
                        room_number=room_number,
                        printer_index=printer_index,
                        printer_model=printer_model,
                        department=department,
                        full_name=printer_name_raw,
                    )

                    # Получаем или создаем пользователя автоматически для избежания потери данных
                    user = User.objects.filter(username__iexact=username).first()
                    if not user:
                        logger.warning(f"User '{username}' not found during import, creating automatically")
                        # Создаем пользователя с минимальными данными
                        user = User.objects.create(
                            username=username,
                            fio=username,  # Временное значение, можно обновить позже
                            is_active=True,
                        )
                        errors.append(f"User '{username}' was automatically created (missing FIO and department)")

                    computer: Computer | None = None
                    computer_name = (event.get("Param4") or "").strip().lower()
                    if computer_name:
                        computer = Computer.objects.filter(name__iexact=computer_name).first()
                        if not computer:
                            computer = Computer.objects.create(name=computer_name)

                    port: Port | None = None
                    port_name = (event.get("Param6") or "").strip().lower()
                    if port_name:
                        port = Port.objects.filter(name__iexact=port_name).first()
                        if not port:
                            port = Port.objects.create(name=port_name)

                    PrintEvent.objects.create(
                        document_id=document_id,
                        document_name=document_name,
                        user=user,
                        printer=printer,
                        job_id=job_id,
                        timestamp=ts,
                        byte_size=byte_size,
                        pages=pages,
                        computer=computer,
                        port=port,
                    )
                    batch_created += 1
                except (ValueError, TypeError, KeyError) as e:
                    # Обрабатываем ожидаемые ошибки валидации отдельно
                    msg = f"Event validation error: {e}"
                    logger.warning(msg, exc_info=True)
                    errors.append(msg)
                except Exception as e:  # noqa: BLE001
                    # Неожиданные ошибки логируются с полным traceback
                    msg = f"Event import error: {e}"
                    logger.error(msg, exc_info=True)
                    errors.append(msg)
            created += batch_created
    
    return {"created": created, "errors": errors}


# -------------------- Query/Stats services --------------------

def get_dashboard_stats(days: int = 30) -> dict[str, Any]:
    from .models import PrintEvent  # local import to avoid cycles at load time

    since = timezone.now() - timezone.timedelta(days=days)
    qs = PrintEvent.objects.select_related("user", "printer").filter(timestamp__gte=since)
    total_pages = qs.aggregate(Sum("pages"))["pages__sum"] or 0
    total_documents = qs.count()
    daily_stats = (
        qs.annotate(date=TruncDate("timestamp"))
        .values("date")
        .annotate(pages=Sum("pages"), documents=Count("id"))
        .order_by("date")
    )
    return {
        "total_pages": total_pages,
        "total_documents": total_documents,
        "daily_stats": daily_stats,
    }


def get_statistics_data(start_date: Any | None, end_date: Any | None) -> dict[str, Any]:
    from .models import PrintEvent, Department  # local import
    from accounts.models import User  # local import

    # Departments (cached aggregate)
    department_cache_key = "department_stats_top"
    department_stats = cache.get(department_cache_key)
    if department_stats is None:
        department_stats = (
            Department.objects.annotate(
                total_pages=Sum("users__print_events__pages"),
                total_documents=Count("users__print_events"),
                total_size=Sum("users__print_events__byte_size"),
            )
            .order_by("-total_pages")
            .all()
        )
        cache.set(department_cache_key, department_stats, 300)

    # Top users
    user_cache_key = "user_stats_top10"
    user_stats = cache.get(user_cache_key)
    if user_stats is None:
        user_stats = (
            User.objects.select_related("department")
            .annotate(
                total_pages=Sum("print_events__pages"),
                total_documents=Count("print_events"),
                total_size=Sum("print_events__byte_size"),
            )
            .order_by("-total_pages")[:10]
        )
        cache.set(user_cache_key, list(user_stats), 300)

    # Print tree
    query = PrintEvent.objects.select_related(
        "printer__department",
        "printer__model",
        "user",
    )
    if start_date:
        query = query.filter(timestamp__gte=start_date)
    if end_date:
        query = query.filter(timestamp__lte=end_date)

    results = (
        query.values(
            "printer__department__code",
            "printer__department__name",
            "printer__model__code",
            "printer__room_number",
            "printer__printer_index",
            "user__fio",
            "document_name",
        )
        .annotate(page_sum=Sum("pages"), last_time=Max("timestamp"))
        .order_by("-page_sum")
    )

    return {
        "department_stats": department_stats,
        "user_stats": user_stats,
        "tree_results": results,
    }


