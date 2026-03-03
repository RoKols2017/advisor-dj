---
title: "Руководство разработчика Print Advisor"
type: archive
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

[Back to README](../../README.md) · [DEVELOPER_GUIDE →](DEVELOPER_GUIDE.md)

# 🛠️ Руководство разработчика Print Advisor

## 📚 Содержание
1. [Архитектура проекта](#архитектура-проекта)
2. [Настройка окружения](#настройка-окружения)
3. [Структура кода](#структура-кода)
4. [Модели данных](#модели-данных)
5. [Представления](#представления)
6. [Формы](#формы)
7. [URL-маршруты](#url-маршруты)
8. [Аутентификация](#аутентификация)
9. [Шаблоны](#шаблоны)
10. [Статические файлы](#статические-файлы)
11. [API](#api)
12. [Тестирование](#тестирование)
13. [Развертывание](#развертывание)
14. [Рекомендации по стилю кода](#рекомендации-по-стилю-кода)

## 🏗️ Архитектура проекта

### Общая структура
Print Advisor построен на основе Django MVT (Model-View-Template) архитектуры:
- **Models**: Определяют структуру данных
- **Views**: Обрабатывают бизнес-логику
- **Templates**: Отвечают за представление данных

### Приложения Django
1. **accounts**
   - Управление пользователями
   - Windows-аутентификация
   - Профили пользователей

2. **printing**
   - Основная бизнес-логика
   - Управление принтерами
   - События печати
   - Статистика

### Взаимодействие компонентов
```
User Request → URLs → Views → Models ↔ Database
                   ↓
                Templates ← Static Files
```

## 🔧 Настройка окружения

### Требования к системе
- Python 3.13+
- Git
- Visual Studio Code (рекомендуется)
- Windows 10/11

### Установка зависимостей
```bash
# Создание виртуального окружения
python -m venv .venv

# Активация окружения
.venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка IDE (VS Code)
1. Установите расширения:
   - Python
   - Django
   - GitLens
   - Black Formatter

2. Настройки (`settings.json`):
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

## 📁 Структура кода

### Основные директории
```
advisor_django/
├── accounts/                  # Приложение аутентификации
│   ├── migrations/           # Миграции базы данных
│   ├── templates/           # Шаблоны приложения
│   ├── __init__.py
│   ├── admin.py            # Настройки админ-панели
│   ├── apps.py            # Конфигурация приложения
│   ├── backends.py        # Бэкенды аутентификации
│   ├── forms.py          # Формы
│   ├── models.py         # Модели данных
│   ├── urls.py          # URL-маршруты
│   ├── views.py         # Представления
│   └── tests.py         # Тесты
│
├── printing/                 # Основное приложение
│   ├── migrations/
│   ├── templates/
│   ├── models/             # Разделенные модели
│   │   ├── __init__.py
│   │   ├── department.py
│   │   ├── printer.py
│   │   ├── print_event.py
│   │   └── building.py
│   ├── admin.py
│   ├── forms.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── templates/               # Общие шаблоны
│   ├── base.html          # Базовый шаблон
│   ├── navbar.html       # Навигация
│   └── footer.html      # Подвал
│
├── static/                # Статические файлы
│   ├── css/
│   ├── js/
│   └── img/
│
├── config/               # Настройки проекта
│   ├── __init__.py
│   ├── settings.py     # Основные настройки
│   ├── urls.py        # Корневые URL
│   └── wsgi.py       # WSGI конфигурация
│
└── manage.py           # Скрипт управления
```

## 📊 Модели данных

### User (accounts/models.py)
```python
class User(AbstractUser):
    fio = models.CharField(max_length=255)
    department = models.ForeignKey('printing.Department', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
```

### Department (printing/models/department.py)
```python
class Department(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Printer (printing/models/printer.py)
```python
class Printer(models.Model):
    name = models.CharField(max_length=255)
    model = models.ForeignKey('PrinterModel', on_delete=models.PROTECT)
    building = models.ForeignKey('Building', on_delete=models.PROTECT)
    room_number = models.CharField(max_length=50)
```

### PrintEvent (printing/models/print_event.py)
```python
class PrintEvent(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    printer = models.ForeignKey('Printer', on_delete=models.PROTECT)
    document_name = models.CharField(max_length=255)
    pages = models.IntegerField()
    timestamp = models.DateTimeField()
```

## 👀 Представления

### Типы представлений
1. **Function-Based Views (FBV)**
   - Для простой логики
   - Когда нужна максимальная гибкость

2. **Class-Based Views (CBV)**
   - Для стандартных операций CRUD
   - Когда нужно наследование

### Примеры представлений

#### Список событий печати (printing/views.py)
```python
class PrintEventListView(LoginRequiredMixin, ListView):
    model = PrintEvent
    template_name = 'printing/event_list.html'
    context_object_name = 'events'
    paginate_by = 50

    def get_queryset(self):
        return PrintEvent.objects.select_related(
            'user',
            'printer'
        ).order_by('-timestamp')
```

#### Статистика (printing/views.py)
```python
@login_required
def statistics_view(request):
    context = {
        'total_events': PrintEvent.objects.count(),
        'total_pages': PrintEvent.objects.aggregate(
            total=Sum('pages')
        )['total'],
        'department_stats': Department.objects.annotate(
            event_count=Count('user__printevent'),
            page_count=Sum('user__printevent__pages')
        )
    }
    return render(request, 'printing/statistics.html', context)
```

## 📝 Формы

### Типы форм
1. **ModelForm**
   - Для форм, связанных с моделями
   - Автоматическая валидация полей

2. **Form**
   - Для произвольных форм
   - Кастомная валидация

### Примеры форм

#### Форма импорта пользователей (printing/forms.py)
```python
class UserImportForm(forms.Form):
    file = forms.FileField(
        label='CSV файл',
        help_text='CSV файл с колонками: username,fio,department_code'
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError('Файл должен быть в формате CSV')
        return file
```

## 🔗 URL-маршруты

### Структура URL

#### Корневые URL (config/urls.py)
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('printing.urls')),
    path('accounts/', include('accounts.urls')),
]
```

#### URL приложения printing (printing/urls.py)
```python
urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('events/', views.PrintEventListView.as_view(), name='event_list'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('import/users/', views.import_users, name='import_users'),
    path('import/events/', views.import_events, name='import_events'),
]
```

## 🔐 Аутентификация

### Windows-аутентификация (accounts/backends.py)
```python
class WindowsAuthBackend:
    def authenticate(self, request, username=None):
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
```

### Настройка аутентификации (config/settings.py)
```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.WindowsAuthBackend',
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
```

## 🎨 Шаблоны

### Базовый шаблон (templates/base.html)
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Print Advisor{% endblock %}</title>
    {% bootstrap_css %}
    {% bootstrap_javascript %}
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    {% include 'navbar.html' %}
    <div class="container mt-4">
        {% bootstrap_messages %}
        {% block content %}{% endblock %}
    </div>
    {% include 'footer.html' %}
</body>
</html>
```

### Наследование шаблонов
```html
{% extends 'base.html' %}

{% block title %}События печати{% endblock %}

{% block content %}
    <h1>События печати</h1>
    {% include 'printing/includes/event_filter.html' %}
    {% include 'printing/includes/event_table.html' %}
{% endblock %}
```

## 📁 Статические файлы

### Структура статических файлов
```
static/
├── css/
│   ├── style.css        # Основные стили
│   └── print.css        # Стили для печати
├── js/
│   ├── main.js         # Основной JavaScript
│   └── charts.js       # Графики и диаграммы
└── img/
    ├── logo.png
    └── icons/
```

### Настройка статических файлов (config/settings.py)
```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
```

## 🔌 API

### REST API (printing/api.py)
```python
from rest_framework import viewsets

class PrintEventViewSet(viewsets.ModelViewSet):
    queryset = PrintEvent.objects.all()
    serializer_class = PrintEventSerializer
    permission_classes = [IsAuthenticated]
```

### Сериализаторы (printing/serializers.py)
```python
from rest_framework import serializers

class PrintEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintEvent
        fields = '__all__'
```

## ✅ Тестирование

### Структура тестов
```
printing/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_forms.py
```

### Пример теста (printing/tests/test_models.py)
```python
from django.test import TestCase
from printing.models import PrintEvent

class PrintEventTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.printer = Printer.objects.create(
            name='Test Printer'
        )

    def test_print_event_creation(self):
        event = PrintEvent.objects.create(
            user=self.user,
            printer=self.printer,
            pages=5
        )
        self.assertEqual(event.pages, 5)
```

## 🚀 Развертывание

### Подготовка к развертыванию
1. Настройка `settings.py`:
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
STATIC_ROOT = '/var/www/static/'
```

2. Сбор статических файлов:
```bash
python manage.py collectstatic
```

### Настройка WSGI/ASGI
```python
# config/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
```

## 📝 Рекомендации по стилю кода

### Python/Django
1. Следуйте PEP 8
2. Используйте типизацию (Python 3.13+)
3. Документируйте сложные функции
4. Используйте говорящие имена переменных

### JavaScript
1. Используйте ES6+
2. Избегайте jQuery там, где можно
3. Используйте async/await

### HTML/CSS
1. Следуйте БЭМ-методологии
2. Используйте семантические теги
3. Поддерживайте адаптивность

## 🔍 Отладка

### Django Debug Toolbar
```python
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### Логирование
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 🔄 Процесс разработки

### Git Flow
1. `main` - продакшн
2. `develop` - разработка
3. `feature/*` - новые функции
4. `hotfix/*` - срочные исправления

### Code Review
1. Создавайте Pull Request
2. Используйте шаблоны PR
3. Проверяйте тесты
4. Следите за качеством кода

### Continuous Integration
1. Запуск тестов
2. Проверка стиля кода
3. Сборка статики
4. Деплой на тестовый сервер

## See Also

- [DEVELOPER_GUIDE](DEVELOPER_GUIDE.md) - следующая страница раздела
- [Deployment](../deployment.md) - актуальные инструкции запуска
- [Troubleshooting](../troubleshooting.md) - диагностика проблем
