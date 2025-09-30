"""
Демон для автоматической загрузки событий печати и пользователей AD в Django.

- Следит за появлением новых файлов в каталоге (WATCH_DIR), указанных через переменные окружения.
- При появлении JSON-файла импортирует события печати (import_print_events_from_json).
- При появлении CSV-файла импортирует пользователей AD (import_users_from_csv).
- После успешной обработки перемещает файл в каталог обработанных (PROCESSED_DIR).
- Все действия и ошибки логируются в отдельный лог-файл (LOG_FILE_NAME).

Запуск:
    python -m printing.print_events_watcher

Требования:
    - Переменные окружения PRINT_EVENTS_WATCH_DIR, PRINT_EVENTS_PROCESSED_DIR
    - LOG_FILE_NAME для отдельного лога демона (по умолчанию print_events_watcher.log)
    - LOG_TO_FILE, LOG_TO_CONSOLE для управления каналами логирования
"""

import logging
import logging.config
import os
import shutil
import sys
import time
import hashlib
from datetime import datetime, timedelta

import django
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Удалить все существующие хендлеры у root-логгера (важно для отключения консоли)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

from config.logging import LOGGING

# Загрузка переменных окружения из .env
load_dotenv()

os.environ['LOG_FILE_NAME'] = 'print_events_watcher.log'
QUARANTINE_DIR = os.getenv('PRINT_EVENTS_QUARANTINE_DIR', './quarantine_dir')

WATCH_DIR = os.getenv('PRINT_EVENTS_WATCH_DIR', './watch_dir')
PROCESSED_DIR = os.getenv('PRINT_EVENTS_PROCESSED_DIR', './processed_dir')

# Политика повторов/дедлайнов (регулируется через ENV)
MAX_RETRIES = int(os.getenv('WATCHER_MAX_RETRIES', '5'))
BACKOFF_BASE = float(os.getenv('WATCHER_BACKOFF_BASE', '2'))  # секунд
BACKOFF_MAX = float(os.getenv('WATCHER_BACKOFF_MAX', '30'))   # секунд
DEADLINE_SECONDS = int(os.getenv('WATCHER_DEADLINE_SECONDS', '300'))

# --- Django setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from printing.importers import import_print_events_from_json, import_users_from_csv

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

class PrintEventHandler(FileSystemEventHandler):
    """
    Обработчик событий файловой системы для демона загрузки печати и пользователей.

    - Импортирует события печати из JSON-файлов.
    - Импортирует пользователей AD из CSV-файлов.
    - Перемещает обработанные файлы в PROCESSED_DIR.
    - Логирует все действия и ошибки.
    """
    def on_created(self, event):
        # Игнорируем каталоги
        if event.is_directory:
            return
        fname = event.src_path
        ext = os.path.splitext(fname)[1].lower()
        # Импорт событий печати из JSON
        if ext == '.json':
            logger.info(f'Найден файл: {fname}')
            started_at = datetime.utcnow()
            for attempt in range(MAX_RETRIES):
                try:
                    # Чтение и импорт событий печати
                    with open(fname, encoding='utf-8-sig') as f:
                        import json
                        events = json.load(f)
                    result = import_print_events_from_json(events)
                    logger.info(f'Загружено: {result}')
                    # Перемещение файла в каталог обработанных
                    dest = os.path.join(PROCESSED_DIR, os.path.basename(fname))
                    shutil.move(fname, dest)
                    logger.info(f'Файл перемещён в {dest}')
                    break
                except PermissionError as e:
                    delay = min(BACKOFF_BASE * (attempt + 1), BACKOFF_MAX)
                    logger.warning(f'Permission denied for {fname} (попытка {attempt+1}/{MAX_RETRIES}): {e}; sleep {delay}s')
                    time.sleep(delay)
                except Exception as e:
                    delay = min(BACKOFF_BASE * (attempt + 1), BACKOFF_MAX)
                    logger.error(f'Ошибка при обработке {fname} (попытка {attempt+1}/{MAX_RETRIES}): {e}', exc_info=True)
                    time.sleep(delay)
                # дедлайн
                if (datetime.utcnow() - started_at) > timedelta(seconds=DEADLINE_SECONDS):
                    logger.error(f'Дедлайн истёк для {fname} — прекращаю повторы')
                    break
            else:
                try:
                    os.makedirs(QUARANTINE_DIR, exist_ok=True)
                    # Имя: {timestamp}-{hash}-{reason}.ext
                    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
                    try:
                        with open(fname, 'rb') as rf:
                            digest = hashlib.sha256(rf.read()).hexdigest()[:12]
                    except Exception:
                        digest = 'nohash'
                    ext = os.path.splitext(fname)[1].lower()
                    reason = 'import_error'
                    quarantine_name = f'{ts}-{digest}-{reason}{ext}'
                    dest = os.path.join(QUARANTINE_DIR, quarantine_name)
                    shutil.move(fname, dest)
                    logger.error(f'Файл перемещён в quarantine: {dest}')
                except Exception as qe:
                    logger.error(f'Не удалось переместить в quarantine {fname}: {qe}', exc_info=True)
        # Импорт пользователей AD из CSV
        elif ext == '.csv':
            logger.info(f'Найден CSV-файл пользователей: {fname}')
            started_at = datetime.utcnow()
            for attempt in range(MAX_RETRIES):
                try:
                    # Чтение и импорт пользователей
                    with open(fname, 'rb') as f:
                        result = import_users_from_csv(f)
                    logger.info(f'Импорт пользователей завершён: {result}')
                    # Перемещение файла в каталог обработанных
                    dest = os.path.join(PROCESSED_DIR, os.path.basename(fname))
                    shutil.move(fname, dest)
                    logger.info(f'CSV-файл перемещён в {dest}')
                    break
                except PermissionError as e:
                    delay = min(BACKOFF_BASE * (attempt + 1), BACKOFF_MAX)
                    logger.warning(f'Permission denied for {fname} (попытка {attempt+1}/{MAX_RETRIES}): {e}; sleep {delay}s')
                    time.sleep(delay)
                except Exception as e:
                    delay = min(BACKOFF_BASE * (attempt + 1), BACKOFF_MAX)
                    logger.error(f'Ошибка при обработке CSV {fname} (попытка {attempt+1}/{MAX_RETRIES}): {e}', exc_info=True)
                    time.sleep(delay)
                if (datetime.utcnow() - started_at) > timedelta(seconds=DEADLINE_SECONDS):
                    logger.error(f'Дедлайн истёк для {fname} — прекращаю повторы')
                    break
            else:
                try:
                    os.makedirs(QUARANTINE_DIR, exist_ok=True)
                    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
                    try:
                        with open(fname, 'rb') as rf:
                            digest = hashlib.sha256(rf.read()).hexdigest()[:12]
                    except Exception:
                        digest = 'nohash'
                    ext = os.path.splitext(fname)[1].lower()
                    reason = 'csv_import_error'
                    quarantine_name = f'{ts}-{digest}-{reason}{ext}'
                    dest = os.path.join(QUARANTINE_DIR, quarantine_name)
                    shutil.move(fname, dest)
                    logger.error(f'CSV-файл перемещён в quarantine: {dest}')
                except Exception as qe:
                    logger.error(f'Не удалось переместить CSV в quarantine {fname}: {qe}', exc_info=True)

if __name__ == "__main__":
    # Гарантируем, что каталоги существуют
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    event_handler = PrintEventHandler()
    observer = Observer()
    # Следим только за WATCH_DIR, без рекурсии
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    logger.info(f'Слежение за {WATCH_DIR}... (Ctrl+C для выхода)')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join() 