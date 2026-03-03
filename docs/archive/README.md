---
title: "Archive Index"
type: archive
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

[← docstrings](docstrings.md) · [Back to README](../../README.md)

# Print Advisor 🖨️

Система мониторинга и анализа печати для организаций. Позволяет отслеживать использование принтеров, собирать статистику и управлять печатной инфраструктурой.

## 🌟 Возможности

- 📊 **Мониторинг печати в реальном времени**
  - Отслеживание всех событий печати
  - Детальная информация о каждом задании печати
  - Статистика использования принтеров

- 👥 **Управление пользователями**
  - Интеграция с Windows-аутентификацией
  - Группировка по отделам
  - Права доступа и роли

- 📈 **Аналитика и отчеты**
  - Статистика по отделам
  - Использование принтеров
  - Объемы печати
  - Экспорт данных

- 🌳 **Иерархическое представление**
  - Древовидная структура данных
  - Группировка по отделам/принтерам/пользователям
  - Детальная информация о каждом уровне

- 📥 **Импорт данных**
  - Импорт пользователей из CSV
  - Импорт событий печати из JSON
  - Поддержка массового импорта

## 🛠️ Технологии

- **Backend**: Python 3.13, Django 5.2
- **Frontend**: Bootstrap 5, JavaScript
- **База данных**: SQLite (с возможностью миграции на PostgreSQL)
- **Аутентификация**: Django Auth + Windows Authentication
- **Дополнительно**: django-tables2, django-filter, django-import-export

## 📋 Требования

- Python 3.13+
- Windows Server/10/11 (для Windows-аутентификации)
- Виртуальное окружение Python (venv)
- Права администратора для Windows-аутентификации

## ⚙️ Установка

1. **Клонирование репозитория**
   ```bash
   git clone <repository-url>
   cd advisor_django
   ```

2. **Создание виртуального окружения**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Установка зависимостей**
   ```bash
   pip install -r requirements.txt
   ```

4. **Настройка переменных окружения**
   Создайте файл `.env` в корневой директории:
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=sqlite:///db.sqlite3
   ```

5. **Применение миграций**
   ```bash
   python manage.py migrate
   ```

6. **Создание суперпользователя**
   ```bash
   python manage.py createsuperuser
   ```

7. **Сбор статических файлов**
   ```bash
   python manage.py collectstatic
   ```

## 🚀 Запуск

1. **Запуск сервера разработки**
   ```bash
   python manage.py runserver
   ```

2. **Доступ к приложению**
   - Веб-интерфейс: http://127.0.0.1:8000
   - Админ-панель: http://127.0.0.1:8000/admin

## 📁 Структура проекта

```
advisor_django/
├── accounts/              # Приложение для управления пользователями
│   ├── models.py         # Модель пользователя
│   └── backends.py       # Windows-аутентификация
├── printing/             # Основное приложение
│   ├── models/          # Модели данных
│   ├── views.py         # Представления
│   ├── urls.py          # URL-маршруты
│   └── admin.py         # Настройки админки
├── templates/           # HTML-шаблоны
├── static/             # Статические файлы
├── config/             # Настройки проекта
└── manage.py          # Скрипт управления
```

## 📊 Модели данных

### User (Пользователь)
- username: имя пользователя Windows
- fio: ФИО пользователя
- department: отдел (FK)
- is_active: активность
- is_staff: права администратора

### Department (Отдел)
- name: название отдела
- code: код отдела
- created_at: дата создания

### Printer (Принтер)
- name: имя принтера
- model: модель принтера (FK)
- building: здание (FK)
- room_number: номер помещения
- printer_index: индекс принтера
- created_at: дата создания

### PrintEvent (Событие печати)
- user: пользователь (FK)
- printer: принтер (FK)
- computer: компьютер (FK)
- port: порт (FK)
- document_name: имя документа
- pages: количество страниц
- byte_size: размер файла
- timestamp: время события

## 🔄 Импорт данных

### Импорт пользователей (CSV)
```csv
username,fio,department_code
user1,Иванов Иван,IT
user2,Петров Петр,HR
```

### Импорт событий печати (JSON)
```json
{
  "events": [
    {
      "user": "username",
      "printer": "printer_name",
      "document": "document.pdf",
      "pages": 5,
      "timestamp": "2025-05-27T12:00:00Z"
    }
  ]
}
```

## 🔒 Безопасность

- Используется Django Security Middleware
- CSRF-защита для всех форм
- Windows-аутентификация (опционально)
- Ограничение доступа по ролям
- Логирование действий пользователей

## 📝 Логирование

Логи сохраняются в директории `logs/`:
- `debug.log`: отладочная информация
- `error.log`: ошибки
- `access.log`: доступ к системе

## 🔧 Настройка

### Настройка Windows-аутентификации
В `settings.py`:
```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.WindowsAuthBackend',
]

WINDOWS_AUTH = {
    'DOMAIN': '',  # Домен (пусто для локального компьютера)
    'REQUIRE_GROUP': None,  # Группа AD (опционально)
}
```

### Настройка базы данных
Для PostgreSQL в `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📈 Мониторинг

- Использование django-debug-toolbar в режиме разработки
- Логирование всех действий
- Отслеживание производительности
- Мониторинг ошибок

## 🤝 Участие в разработке

1. Fork репозитория
2. Создайте ветку для новой функции
3. Внесите изменения
4. Отправьте Pull Request

## 📫 Поддержка

При возникновении проблем:
1. Проверьте раздел Issues
2. Создайте новый Issue с описанием проблемы
3. Приложите логи и описание окружения

## 📄 Лицензия

MIT License. См. файл LICENSE для деталей.

## 🙏 Благодарности

- Django Team
- Сообщество Python
- Всем контрибьюторам проекта

## See Also

- [docstrings](docstrings.md) - соседняя страница раздела
- [Deployment](../deployment.md) - актуальные инструкции запуска
- [Troubleshooting](../troubleshooting.md) - диагностика проблем
