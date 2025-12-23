# Итоги развертывания Print Advisor

**Дата:** 2025-12-20  
**Статус:** ✅ Успешно развернуто

## Выполненные действия

### 1. Создана структура каталогов
- ✅ `data/watch/` - каталог для мониторинга файлов с Windows-сервера
- ✅ `data/processed/` - каталог для обработанных файлов
- ✅ `data/quarantine/` - каталог для файлов с ошибками
- ✅ `logs/` - каталог для логов приложения

### 2. Сгенерированы безопасные пароли
- ✅ **SECRET_KEY**: `b7GRoqLtyhsDXzjPW1QanWkwqk7xKpGllHADQ7M5yRCyohHO7EpSB0oVLB2B3Omi7m4` (67 символов)
- ✅ **POSTGRES_PASSWORD**: `Lg4DVvuQ78Nvw3oztEr-TCHEz4ZukI_nWwngPb4XGR8t_XUdDFjivnKYPOG1-SMFk_o` (67 символов)

### 3. Создан .env файл
- ✅ Все необходимые переменные окружения настроены
- ✅ Пароли сохранены в `.env` (права доступа: 600)

### 4. Собраны Docker-образы
- ✅ `advisor-dj-web` - веб-сервер (Django + Gunicorn)
- ✅ `advisor-dj-watcher` - демон мониторинга каталога
- ✅ `postgres:15` - база данных

### 5. Запущены контейнеры
- ✅ **advisor-db** (PostgreSQL) - статус: `healthy`
- ✅ **advisor-web** (Django) - статус: `healthy`, порт: `8001`
- ✅ **advisor-watcher** (мониторинг) - статус: `healthy`

### 6. Выполнены миграции БД
- ✅ Все миграции применены успешно (включая новые: `0004_add_unique_job_id`, `0005_add_user_printer_indexes`)

### 7. Проверена работоспособность
- ✅ Health check: `http://localhost:8001/health/` - работает
- ✅ Все сервисы в статусе `healthy`

## Текущая конфигурация

### Порты
- **Web-приложение**: `http://localhost:8001` (порт изменен с 8000, т.к. 8000 занят Portainer)
- **PostgreSQL**: `localhost:5432`

### Доступ к приложению
```bash
# Веб-интерфейс
http://localhost:8001

# Админка Django
http://localhost:8001/admin
```

### Полезные команды

```bash
# Просмотр статуса
docker compose ps

# Просмотр логов
docker compose logs -f
docker compose logs watcher -f
docker compose logs web -f

# Остановка
docker compose down

# Запуск
docker compose up -d

# Перезапуск
docker compose restart

# Создание суперпользователя
docker compose exec web python manage.py createsuperuser
```

## Следующие шаги для работы в ЛВС

### 1. Монтирование Windows-шары (когда сервер будет в ЛВС)

```bash
# Установить cifs-utils
sudo apt-get install cifs-utils

# Создать точку монтирования
sudo mkdir -p /mnt/printshare

# Смонтировать Windows-шару
sudo mount -t cifs //windows-server/share /mnt/printshare \
  -o username=user,password=pass,uid=1000,gid=1000,iocharset=utf8

# Обновить docker-compose.yml для watcher:
# volumes:
#   - /mnt/printshare:/app/data/watch:ro
```

### 2. Сохранение образов для переноса (если нужно)

```bash
# Сохранить образы в архив
docker save \
  advisor-dj-web:latest \
  advisor-dj-watcher:latest \
  postgres:15 \
  -o advisor-dj-images.tar

# На целевой машине загрузить:
docker load -i advisor-dj-images.tar
```

### 3. Настройка для продакшена

Перед переключением в ЛВС обновите в `.env`:
- `ALLOWED_HOSTS` - добавьте IP-адрес сервера в ЛВС
- `DEBUG=0` - уже установлено
- Проверьте, что все пароли сохранены безопасно

## Важная информация

### Пароли и секреты
Все пароли сохранены в файле `.env` с правами доступа 600.  
**ВАЖНО**: Сохраните этот файл в безопасном месте перед переключением сервера в ЛВС!

### Структура данных
- **База данных**: хранится в Docker volume `advisor-dj_pgdata`
- **Логи**: хранятся в Docker volume `advisor-dj_logs`
- **Файлы для обработки**: хранятся в Docker volume `advisor-dj_data`

### Мониторинг
Watcher автоматически следит за каталогом `/app/data/watch` и обрабатывает:
- **JSON-файлы** → импорт событий печати
- **CSV-файлы** → импорт пользователей

Обработанные файлы перемещаются в `processed/`, файлы с ошибками - в `quarantine/`.

## Статус: ✅ Готово к работе

Все контейнеры запущены и работают корректно. Приложение готово к использованию!


