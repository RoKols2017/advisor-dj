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
    manufacturer = normalized.split()[0]
    return PrinterModel.objects.create(code=normalized, manufacturer=manufacturer)


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
                except Exception as e:  # noqa: BLE001 - логируем и продолжаем пакет
                    msg = f"Row error {row}: {e}"
                    logger.error(msg)
                    errors.append(msg)
    except Exception as e:  # noqa: BLE001
        msg = f"Users import failed: {e}"
        logger.error(msg)
        errors.append(msg)
    return {"created": created, "errors": errors}


def import_print_events(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    created = 0
    errors: list[str] = []
    for event in events:
        try:
            with transaction.atomic():
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

                if PrintEvent.objects.filter(job_id=job_id).exists():
                    continue

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

                try:
                    user = User.objects.get(username__iexact=username)
                except User.DoesNotExist:
                    errors.append(f"User not found: {username}")
                    continue

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
                created += 1
        except Exception as e:  # noqa: BLE001
            msg = f"Event import error: {e}"
            logger.error(msg)
            errors.append(msg)
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


