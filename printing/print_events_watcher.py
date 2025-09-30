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

import os
import time
import shutil
import sys
import django
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import logging
import logging.config

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
            for attempt in range(5):
                try:
                    # Чтение и импорт событий печати
                    with open(fname, 'r', encoding='utf-8-sig') as f:
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
                    logger.warning(f'Permission denied for {fname} (попытка {attempt+1}/5): {e}')
                    time.sleep(2 * (attempt + 1))
                except Exception as e:
                    logger.error(f'Ошибка при обработке {fname} (попытка {attempt+1}/5): {e}', exc_info=True)
                    time.sleep(2 * (attempt + 1))
            else:
                try:
                    os.makedirs(QUARANTINE_DIR, exist_ok=True)
                    dest = os.path.join(QUARANTINE_DIR, os.path.basename(fname))
                    shutil.move(fname, dest)
                    logger.error(f'Файл перемещён в quarantine: {dest}')
                except Exception as qe:
                    logger.error(f'Не удалось переместить в quarantine {fname}: {qe}', exc_info=True)
        # Импорт пользователей AD из CSV
        elif ext == '.csv':
            logger.info(f'Найден CSV-файл пользователей: {fname}')
            for attempt in range(5):
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
                    logger.warning(f'Permission denied for {fname} (попытка {attempt+1}/5): {e}')
                    time.sleep(2 * (attempt + 1))
                except Exception as e:
                    logger.error(f'Ошибка при обработке CSV {fname} (попытка {attempt+1}/5): {e}', exc_info=True)
                    time.sleep(2 * (attempt + 1))
            else:
                try:
                    os.makedirs(QUARANTINE_DIR, exist_ok=True)
                    dest = os.path.join(QUARANTINE_DIR, os.path.basename(fname))
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