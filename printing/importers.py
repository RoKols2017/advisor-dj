import csv
import logging
from datetime import datetime
from django.db import transaction
from django.db.models import Q
from .models import Department, PrintEvent, Printer, PrinterModel, Building, Computer, Port
from accounts.models import User
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger('import')

def import_users_from_csv(file):
    """
    Импорт пользователей из CSV файла.
    Формат: SamAccountName,DisplayName,OU
    """
    created = 0
    errors = []
    
    try:
        decoded_file = file.read().decode('utf-8-sig')
        reader = csv.DictReader(decoded_file.splitlines())
        
        with transaction.atomic():
            for row in reader:
                try:
                    username = row.get('SamAccountName', '').strip()
                    fio = row.get('DisplayName', '').strip()
                    dept_code = row.get('OU', '').strip().lower()
                    
                    if not dept_code:
                        continue  # Пропускаем записи без OU
                    
                    # Получаем или создаем отдел
                    department, _ = Department.objects.get_or_create(
                        code__iexact=dept_code,
                        defaults={
                            'code': dept_code,
                            'name': dept_code.upper()
                        }
                    )
                    
                    # Получаем или создаем пользователя
                    user, created_user = User.objects.update_or_create(
                        username__iexact=username,
                        defaults={
                            'username': username,
                            'fio': fio or username,
                            'department': department,
                            'is_active': True
                        }
                    )
                    
                    if created_user:
                        created += 1
                        
                except Exception as e:
                    error_msg = f"Ошибка в строке {row}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
    except Exception as e:
        error_msg = f"Ошибка при импорте пользователей: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        
    return {
        'created': created,
        'errors': errors
    }

def import_print_events_from_json(events):
    """
    Импорт событий печати из JSON.
    """
    created = 0
    errors = []
    
    for event in events:
        try:
            with transaction.atomic():
                # Получаем основные данные события
                username = (event.get('Param3') or '').strip().lower()
                document_name = event.get('Param2', '')
                document_id = int(event.get('Param1') or 0)
                byte_size = int(event.get('Param7') or 0)
                pages = int(event.get('Param8') or 0)
                timestamp_ms = int(event.get('TimeCreated').replace('/Date(', '').replace(')/',''))
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                # Приводим к aware если нужно
                if settings.USE_TZ and timezone.is_naive(timestamp):
                    timestamp = timezone.make_aware(timestamp, timezone.get_default_timezone())
                job_id = event.get('JobID') or 'UNKNOWN'
                
                # Проверяем существование события
                if PrintEvent.objects.filter(job_id=job_id).exists():
                    continue
                
                # Парсим имя принтера
                printer_name = (event.get('Param5') or '').strip().lower()
                printer_parts = printer_name.split('-')
                if len(printer_parts) != 5:
                    errors.append(f"Неверный формат принтера: {printer_name}")
                    continue
                
                model_code, bld_code, dept_code, room_number, printer_index = printer_parts
                printer_index = int(printer_index)
                
                # Получаем или создаем здание
                building, _ = Building.objects.get_or_create(
                    code__iexact=bld_code,
                    defaults={
                        'code': bld_code,
                        'name': bld_code.upper()
                    }
                )
                
                # Получаем или создаем отдел
                department, _ = Department.objects.get_or_create(
                    code__iexact=dept_code,
                    defaults={
                        'code': dept_code,
                        'name': dept_code.upper()
                    }
                )
                
                # Получаем или создаем модель принтера
                printer_model, _ = PrinterModel.objects.get_or_create(
                    code__iexact=model_code,
                    defaults={
                        'code': model_code,
                        'manufacturer': model_code.split()[0],
                        'model': model_code
                    }
                )
                
                # Получаем или создаем принтер
                printer, _ = Printer.objects.get_or_create(
                    building=building,
                    room_number__iexact=room_number,
                    printer_index=printer_index,
                    defaults={
                        'name': printer_name,
                        'model': printer_model,
                        'department': department,
                        'room_number': room_number,
                        'printer_index': printer_index,
                        'is_active': True
                    }
                )
                
                # Получаем пользователя
                try:
                    user = User.objects.get(username__iexact=username)
                except User.DoesNotExist:
                    errors.append(f"Пользователь не найден: {username}")
                    continue
                
                # Обрабатываем компьютер
                computer = None
                computer_name = (event.get('Param4') or '').strip().lower()
                if computer_name:
                    computer, created_computer = Computer.objects.get_or_create(
                        name__iexact=computer_name,
                        defaults={'name': computer_name}
                    )
                
                # Обрабатываем порт
                port = None
                port_name = (event.get('Param6') or '').strip().lower()
                if port_name:
                    port, created_port = Port.objects.get_or_create(
                        name__iexact=port_name,
                        defaults={'name': port_name}
                    )
                
                # Создаем событие печати
                PrintEvent.objects.create(
                    document_id=document_id,
                    document_name=document_name,
                    user=user,
                    printer=printer,
                    job_id=job_id,
                    timestamp=timestamp,
                    byte_size=byte_size,
                    pages=pages,
                    computer=computer,
                    port=port
                )
                created += 1
                
        except Exception as e:
            error_msg = f"Ошибка при импорте события: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            
    return {
        'created': created,
        'errors': errors
    } 