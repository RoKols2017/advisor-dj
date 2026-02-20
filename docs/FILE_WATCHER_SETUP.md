---
title: "Настройка загрузчика файлов (File Watcher)"
type: guide
status: draft
last_verified: "2026-02-20"
verified_against_commit: "latest"
owner: "@rom"
---

# Настройка загрузчика файлов (File Watcher)

## Обзор

Загрузчик файлов (`print_events_watcher`) автоматически обрабатывает файлы, скопированные в каталог `data/watch/`:
- **JSON файлы** (.json) → импорт событий печати
- **CSV файлы** (.csv) → импорт пользователей AD

После обработки файлы перемещаются:
- **Успешно обработанные** → `data/processed/`
- **Ошибочные** → `data/quarantine/`

## Структура каталогов

```
data/
├── watch/          # Каталог для загрузки файлов (мониторится watcher)
├── processed/      # Успешно обработанные файлы
└── quarantine/     # Файлы с ошибками обработки
```

## Права доступа

### Текущие требования

Watcher работает от имени пользователя `appuser` (UID 999, GID 999) внутри контейнера.

**Требуемые права:**
- Все три каталога (`watch`, `processed`, `quarantine`) должны быть доступны для чтения и записи пользователю контейнера

### Команды для настройки прав

#### Вариант 1: Права 777 (только для локальной разработки)

```bash
sudo chmod 777 data/watch
sudo chmod 777 data/processed
sudo chmod 777 data/quarantine
```

**Преимущества:**
- Простота настройки
- Гарантированная работа
- Подходит для локальной разработки

**Недостатки:**
- Менее безопасно (все пользователи могут писать)

#### Вариант 2: Изменить владельца

```bash
sudo chown -R 999:999 data/watch
sudo chown -R 999:999 data/processed
sudo chown -R 999:999 data/quarantine
```

**Преимущества:**
- Более безопасно (только владелец может писать)
- Можно использовать стандартные права (755)

**Недостатки:**
- Требуется sudo для изменения владельца

#### Вариант 3: Комбинация (владелец + права 775)

```bash
sudo chown -R 999:999 /home/roman/project/advisor-dj/data/{watch,processed,quarantine}
sudo chmod 775 /home/roman/project/advisor-dj/data/{watch,processed,quarantine}
```

**Преимущества:**
- Баланс между безопасностью и удобством
- Группа может писать, остальные только читать

### Проверка прав доступа

Проверить текущие права:
```bash
ls -ld data/watch data/processed data/quarantine
```

Проверить права изнутри контейнера:
```bash
docker compose exec watcher python -c "import os; dirs = ['/app/data/watch', '/app/data/processed', '/app/data/quarantine']; [print(f'{d}: R={os.access(d, os.R_OK)} W={os.access(d, os.W_OK)} X={os.access(d, os.X_OK)}') for d in dirs]"
```

## Как работает загрузчик

### Обработка файлов

1. **При старте watcher:**
   - Обрабатываются все существующие файлы в `data/watch/`
   - Это гарантирует обработку файлов, скопированных до запуска watcher

2. **Во время работы:**
   - Watcher следит за появлением новых файлов через события файловой системы
   - Каждый новый файл обрабатывается автоматически

### Процесс обработки

Для каждого файла:

1. **Обнаружение файла**
   - Watcher находит файл с расширением .json или .csv

2. **Импорт данных**
   - JSON → `import_print_events_from_json()` → события печати
   - CSV → `import_users_from_csv()` → пользователи AD

3. **Перемещение файла**
   - **Успех** → файл перемещается в `data/processed/`
   - **Ошибка** → файл перемещается в `data/quarantine/` с уникальным именем:
     ```
     {timestamp}-{hash}-{reason}.{ext}
     ```
     Пример: `20251223T160001Z-deab2b87b35a-import_error.json`

### Повторы и обработка ошибок

- **Максимум попыток**: 5 (настраивается через `WATCHER_MAX_RETRIES`)
- **Экспоненциальная задержка**: от 2 до 30 секунд между попытками
- **Дедлайн**: 300 секунд (5 минут) на весь процесс обработки файла

## Мониторинг работы

### Просмотр логов

```bash
# Последние логи watcher
docker compose logs watcher --tail=50

# Логи в реальном времени
docker compose logs watcher -f

# Логи из файла (внутри контейнера)
docker compose exec watcher tail -100 /app/logs/project.log | grep -i "watcher\|import\|обработан"
```

### Проверка статуса

```bash
# Использовать скрипт проверки статуса
./scripts/check_import_status.sh

# Или вручную
ls -lh data/watch/      # Файлы ожидающие обработки
ls -lh data/processed/  # Обработанные файлы
ls -lh data/quarantine/ # Файлы с ошибками
```

### Проверка базы данных

```bash
# Количество пользователей
docker compose exec web python manage.py shell -c "from accounts.models import User; print('Пользователей:', User.objects.count())"

# Количество событий печати
docker compose exec web python manage.py shell -c "from printing.models import PrintEvent; print('Событий:', PrintEvent.objects.count())"
```

## Загрузка файлов

Для production рекомендуется использовать транзитную загрузку (inbox -> ingest -> watch), а не прямую запись удаленных серверов в watcher-каталог. Подробная схема: `docs/how-to/transit-ingest-pipeline.md`.

### Ручная загрузка

```bash
# Копирование файлов в каталог watch
cp /path/to/file.json data/watch/
cp /path/to/file.csv data/watch/
```

### Автоматическая загрузка (через транзит)

Используйте ingest-процесс на Linux:

```bash
sudo cp infrastructure/systemd/advisor-ingest.env.example /etc/default/advisor-ingest
sudo cp infrastructure/systemd/advisor-ingest-mover.service /etc/systemd/system/
sudo cp infrastructure/systemd/advisor-ingest-mover.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now advisor-ingest-mover.timer
```

Скрипт ingestion: `scripts/ingest_mover.sh`.
Он обрабатывает только `*.json` и `*.csv`, проверяет стабильность файла, выполняет дедупликацию и атомарно переносит файлы в watcher queue.

## Переменные окружения

Настройка через переменные окружения (в `docker-compose.yml` или `.env`):

- `PRINT_EVENTS_WATCH_DIR` - каталог для мониторинга (по умолчанию: `/app/data/watch`)
- `PRINT_EVENTS_PROCESSED_DIR` - каталог для обработанных файлов (по умолчанию: `/app/data/processed`)
- `PRINT_EVENTS_QUARANTINE_DIR` - каталог для ошибочных файлов (по умолчанию: `/app/data/quarantine`)
- `WATCHER_MAX_RETRIES` - максимальное количество попыток (по умолчанию: 5)
- `WATCHER_BACKOFF_BASE` - базовая задержка между попытками в секундах (по умолчанию: 2)
- `WATCHER_BACKOFF_MAX` - максимальная задержка в секундах (по умолчанию: 30)
- `WATCHER_DEADLINE_SECONDS` - дедлайн обработки файла в секундах (по умолчанию: 300)

## Устранение проблем

### Файлы не обрабатываются

1. **Проверить права доступа:**
   ```bash
   ls -ld data/watch data/processed data/quarantine
   ```
   Должны быть 777 или владелец 999:999

2. **Проверить что watcher работает:**
   ```bash
   docker compose ps watcher
   docker compose logs watcher --tail=20
   ```

3. **Проверить что файлы видны в контейнере:**
   ```bash
   docker compose exec watcher ls -la /app/data/watch/
   ```

### Файлы остаются в watch

- **Если файлы были скопированы до запуска watcher:** они будут обработаны при следующем запуске watcher (функция `process_existing_files()`)
- **Если файлы обрабатываются но не перемещаются:** проверить права на `processed` и `quarantine`
- **Если ошибки обработки:** проверить логи и файлы в `quarantine`

### Ошибки Permission denied

1. Установить права 777 на все каталоги (см. раздел "Права доступа")
2. Проверить что каталоги существуют
3. Перезапустить watcher после изменения прав:
   ```bash
   docker compose restart watcher
   ```

## Примеры использования

### Полный цикл обработки файла

```bash
# 1. Копирование файла
cp users.csv data/watch/

# 2. Проверка логов (в реальном времени)
docker compose logs watcher -f

# 3. Проверка что файл обработан
ls -lh data/processed/users.csv

# 4. Проверка импорта в БД
docker compose exec web python manage.py shell -c "from accounts.models import User; print(User.objects.count())"
```

### Очистка старых обработанных файлов

```bash
# Переместить старые файлы в архив
find data/processed -type f -mtime +30 -exec mv {} data/archive/ \;
```

### Мониторинг через скрипт

```bash
# Запуск скрипта проверки статуса
./scripts/check_import_status.sh
```




