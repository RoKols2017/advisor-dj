---
title: "Руководство по деплою Print Advisor"
type: guide
status: draft
last_verified: "2026-02-18"
verified_against_commit: "latest"
owner: "@rom"
---

[← Deploy Plan](DEPLOY_PLAN.md) · [Back to README](../README.md) · [Nginx Setup →](NGINX_SETUP.md)

# 🚀 Руководство по деплою Print Advisor

## 🏗️ **Что такое деплой и зачем он нужен?**

**Деплой** — это процесс развёртывания твоего приложения на сервере, чтобы пользователи могли им пользоваться. В твоём случае это Django-приложение для мониторинга печати.

## 📁 **Основные файлы, управляющие деплоем:**

### 1. **Dockerfile** — "рецепт" для создания образа веб-приложения
### 2. **Dockerfile.watcher** — "рецепт" для создания образа демона-наблюдателя
### 3. **docker-compose.yml** — конфигурация для разработки
### 4. **docker-compose.prod.yml** — конфигурация для продакшена
### 5. **Makefile** — команды-сокращения для удобства
### 6. **scripts/smoke.sh** — автоматические проверки после деплоя

---

## 🔧 **Пошаговый разбор процесса деплоя:**

### **ШАГ 1: Подготовка окружения**

#### **1.1 Создание .env.prod файла**
```bash
# Копируем шаблон и настраиваем под себя
cp .env.prod.template .env.prod
# Редактируем секреты, пароли, пути
nano .env.prod
```

**Что происходит:** Создаётся файл с переменными окружения для продакшена (пароли, ключи, настройки).

#### **1.2 Сборка Docker образов**
```bash
make build
# или
docker compose build
```

**Что происходит:**
- Docker читает `Dockerfile` и `Dockerfile.watcher`
- Создаёт два образа: `advisor-web` и `advisor-watcher`
- В каждом образе устанавливается Python, зависимости, копируется код

**Детали Dockerfile:**
```dockerfile
# Базовый образ Python 3.13
FROM python:3.13-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y build-essential libpq-dev curl

# Создаём пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Копируем код и устанавливаем зависимости
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Собираем статические файлы Django
RUN python manage.py collectstatic --noinput

# Запускаем от имени обычного пользователя (не root)
USER appuser
```

### **ШАГ 2: Запуск сервисов**

#### **2.1 Запуск всех сервисов**
```bash
make up
# или
docker compose -f docker-compose.prod.yml up -d
```

**Что происходит:**
1. **База данных (PostgreSQL):**
   - Создаётся контейнер `advisor-db`
   - Инициализируется база данных
   - Настраивается пользователь и пароль

2. **Веб-приложение:**
   - Создаётся контейнер `advisor-web`
   - Запускается Gunicorn (веб-сервер)
   - Ждёт готовности базы данных

3. **Демон-наблюдатель:**
   - Создаётся контейнер `advisor-watcher`
   - Запускается скрипт мониторинга файлов
   - Ждёт готовности веб-приложения

#### **2.2 Проверка зависимостей (depends_on)**
```yaml
web:
  depends_on:
    db:
      condition: service_healthy  # Ждём, пока БД не станет здоровой

watcher:
  depends_on:
    web:
      condition: service_healthy  # Ждём, пока веб не станет здоровым
    db:
      condition: service_healthy
```

**Что происходит:** Docker Compose автоматически ждёт готовности зависимых сервисов перед запуском следующих.

### **ШАГ 3: Инициализация базы данных**

#### **3.1 Миграции**
```bash
make migrate
# или
docker compose exec web python manage.py migrate
```

**Что происходит:**
- Django создаёт таблицы в базе данных
- Применяет все миграции (изменения схемы БД)
- Создаёт индексы для оптимизации

#### **3.2 Сбор статических файлов**
```bash
make collectstatic
# или
docker compose exec web python manage.py collectstatic --noinput
```

**Что происходит:**
- Django собирает CSS, JS, изображения в одну папку
- Готовит файлы для раздачи веб-сервером

### **ШАГ 4: Проверка работоспособности (Smoke Tests)**

#### **4.1 Автоматические проверки**
```bash
make smoke
# или
./scripts/smoke.sh
```

**Что происходит в smoke.sh:**
1. **Проверка здоровья сервисов:**
   ```bash
   docker compose exec -T web curl -f -s http://localhost:8000/health/
   ```

2. **Проверка основных страниц:**
   ```bash
   docker compose exec -T web curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
   docker compose exec -T web curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/login/
   ```

3. **Проверка Django:**
   ```bash
   docker compose exec web python manage.py check --deploy
   docker compose exec web python manage.py migrate --check
   ```

4. **Проверка демона:**
   ```bash
   docker compose exec watcher pgrep -f "printing.print_events_watcher"
   ```

---

## 🔄 **Как работают команды в Makefile:**

### **Основные команды:**
```makefile
build:        # Собирает Docker образы
up:           # Запускает все сервисы в фоне
down:         # Останавливает все сервисы
logs:         # Показывает логи всех сервисов
smoke:        # Запускает проверки
migrate:      # Применяет миграции БД
clean:        # Удаляет контейнеры и данные
```

### **Пример работы команды `make up`:**
```bash
make up
# ↓ Выполняется:
docker compose up -d
# ↓ Что происходит:
# 1. Читается docker-compose.yml
# 2. Создаются/запускаются контейнеры
# 3. Настраивается сеть между контейнерами
# 4. Монтируются тома (папки)
# 5. Проверяются health checks
```

---

## 🌐 **Сетевая архитектура:**

### **Внутренняя сеть Docker:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   advisor-web   │    │  advisor-watcher│    │   advisor-db    │
│   (порт 8000)   │◄──►│   (демон)       │◄──►│   (порт 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ advisor-network │
                    │   (bridge)      │
                    └─────────────────┘
```

### **Внешние порты:**
- **80** — веб-интерфейс через Nginx reverse proxy
- **5432** — база данных (только внутри Docker)

---

## 📂 **Тома (Volumes) — постоянное хранение:**

### **Что такое тома:**
```yaml
volumes:
  pgdata:    # Данные PostgreSQL
  logs:      # Логи приложения
  data:      # Файлы для обработки
```

### **Зачем нужны:**
- **pgdata** — данные БД не теряются при перезапуске
- **logs** — логи сохраняются для анализа
- **data** — файлы для импорта (watch/processed/quarantine)

---

## 🔍 **Health Checks — проверки здоровья:**

### **Как работают:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 30s    # Проверяем каждые 30 секунд
  timeout: 10s     # Ждём ответа 10 секунд
  retries: 3       # 3 попытки перед "unhealthy"
  start_period: 40s # Даём 40 секунд на запуск
```

### **Что проверяется:**
- **Web:** доступность `/health/` endpoint
- **Watcher:** запущен ли процесс демона
- **DB:** готовность PostgreSQL

---

## 🚀 **Полный процесс деплоя (команды):**

```bash
# 1. Подготовка
cp .env.prod.template .env.prod
nano .env.prod  # Настраиваем секреты

# 2. Сборка
make build

# 3. Запуск
make up
make nginx-up

# 4. Инициализация
make migrate
make collectstatic

# 5. Проверка
make smoke

# 6. Мониторинг
make logs
make health
```

---

## 🛠️ **Отладка проблем:**

### **Проверка статуса:**
```bash
make status        # Статус контейнеров
make health        # Здоровье сервисов
make logs-web      # Логи веб-приложения
make logs-watcher  # Логи демона
make logs-db       # Логи базы данных
```

### **Вход в контейнер:**
```bash
docker compose exec web bash      # В веб-контейнер
docker compose exec watcher bash  # В контейнер демона
docker compose exec db psql -U advisor -d advisor  # В базу данных
```

---

## 📋 **Резюме для новичка:**

1. **Docker** — упаковывает приложение в "коробки" (контейнеры)
2. **Docker Compose** — управляет несколькими контейнерами как единым целым
3. **Makefile** — упрощает команды (вместо длинных docker compose команд)
4. **Health Checks** — автоматически проверяют, что всё работает
5. **Volumes** — сохраняют данные между перезапусками
6. **Smoke Tests** — автоматически проверяют работоспособность после деплоя

Это как **оркестр**: каждый инструмент (контейнер) играет свою партию, а дирижёр (Docker Compose) управляет всем процессом!

---

## 📚 **Дополнительные ресурсы:**

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)

---

*Создано: $(date)*  
*Версия: 1.0*

## See Also

- [Getting Started](getting-started.md) - базовый путь запуска
- [Deployment](deployment.md) - актуальный сценарий деплоя
- [Troubleshooting](troubleshooting.md) - диагностика типовых проблем
