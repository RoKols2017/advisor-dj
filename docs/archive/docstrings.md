---
title: "Примеры Docstrings для Print Advisor"
type: archive
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

[← DEVELOPER_GUIDE](DEVELOPER_GUIDE.md) · [Back to README](../../README.md) · [README →](README.md)

# 📝 Примеры Docstrings для Print Advisor

## 📊 Модели

### User (accounts/models.py)
```python
class User(AbstractUser):
    """
    Расширенная модель пользователя Django с дополнительными полями.

    Attributes:
        fio (str): ФИО пользователя
        department (Department): Отдел, к которому принадлежит пользователь

    Example:
        >>> user = User.objects.create(
        ...     username='ivanov',
        ...     fio='Иванов Иван Иванович',
        ...     department=Department.objects.get(code='IT')
        ... )
    """
    fio = models.CharField(max_length=255)
    department = models.ForeignKey('printing.Department', on_delete=models.SET_NULL, null=True)
```

### Department (printing/models/department.py)
```python
class Department(models.Model):
    """
    Модель отдела организации.

    Attributes:
        name (str): Полное название отдела
        code (str): Уникальный код отдела
        created_at (datetime): Дата и время создания записи

    Methods:
        get_employee_count(): Возвращает количество сотрудников в отделе
        get_print_statistics(): Возвращает статистику печати по отделу

    Example:
        >>> dept = Department.objects.create(
        ...     name='Отдел информационных технологий',
        ...     code='IT'
        ... )
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_employee_count(self):
        """Возвращает количество сотрудников в отделе."""
        return self.user_set.count()

    def get_print_statistics(self):
        """
        Возвращает статистику печати по отделу.

        Returns:
            dict: Словарь со статистикой:
                {
                    'total_events': int,
                    'total_pages': int,
                    'avg_pages_per_user': float
                }
        """
        stats = self.user_set.aggregate(
            total_events=Count('printevent'),
            total_pages=Sum('printevent__pages')
        )
        employee_count = self.get_employee_count()
        if employee_count > 0:
            stats['avg_pages_per_user'] = stats['total_pages'] / employee_count
        return stats
```

### PrintEvent (printing/models/print_event.py)
```python
class PrintEvent(models.Model):
    """
    Модель события печати.

    Attributes:
        user (User): Пользователь, инициировавший печать
        printer (Printer): Принтер, на котором производилась печать
        document_name (str): Имя печатаемого документа
        pages (int): Количество страниц
        timestamp (datetime): Дата и время события

    Methods:
        get_cost(): Возвращает стоимость печати
        get_department(): Возвращает отдел пользователя
        format_timestamp(): Возвращает отформатированную дату/время

    Example:
        >>> event = PrintEvent.objects.create(
        ...     user=user,
        ...     printer=printer,
        ...     document_name='report.pdf',
        ...     pages=5,
        ...     timestamp=timezone.now()
        ... )
    """
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    printer = models.ForeignKey('Printer', on_delete=models.PROTECT)
    document_name = models.CharField(max_length=255)
    pages = models.IntegerField()
    timestamp = models.DateTimeField()

    def get_cost(self):
        """
        Рассчитывает стоимость печати.

        Returns:
            Decimal: Стоимость печати в рублях
        """
        return Decimal(self.pages) * self.printer.cost_per_page

    def get_department(self):
        """Возвращает отдел пользователя."""
        return self.user.department

    def format_timestamp(self):
        """
        Форматирует дату/время события.

        Returns:
            str: Отформатированная дата/время
        """
        return self.timestamp.strftime('%d.%m.%Y %H:%M:%S')
```

## 👀 Представления

### PrintEventListView (printing/views.py)
```python
class PrintEventListView(LoginRequiredMixin, ListView):
    """
    Представление для отображения списка событий печати.

    Attributes:
        model (Model): Модель PrintEvent
        template_name (str): Путь к шаблону
        context_object_name (str): Имя переменной контекста
        paginate_by (int): Количество элементов на странице

    Methods:
        get_queryset(): Возвращает отфильтрованный QuerySet
        get_context_data(): Добавляет дополнительные данные в контекст

    Example:
        URL Configuration:
        path('events/', PrintEventListView.as_view(), name='event_list')
    """
    model = PrintEvent
    template_name = 'printing/event_list.html'
    context_object_name = 'events'
    paginate_by = 50

    def get_queryset(self):
        """
        Возвращает QuerySet с предзагруженными связанными объектами.

        Returns:
            QuerySet: Отфильтрованный и отсортированный список событий
        """
        return PrintEvent.objects.select_related(
            'user',
            'printer'
        ).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        """
        Добавляет статистику в контекст.

        Returns:
            dict: Расширенный контекст шаблона
        """
        context = super().get_context_data(**kwargs)
        context['total_pages'] = self.get_queryset().aggregate(
            total=Sum('pages')
        )['total']
        return context
```

## 📝 Формы

### UserImportForm (printing/forms.py)
```python
class UserImportForm(forms.Form):
    """
    Форма для импорта пользователей из CSV файла.

    Fields:
        file (FileField): Поле для загрузки CSV файла

    Methods:
        clean_file(): Валидация файла
        process_file(): Обработка загруженного файла

    Example:
        >>> form = UserImportForm(request.POST, request.FILES)
        >>> if form.is_valid():
        ...     form.process_file()
    """
    file = forms.FileField(
        label='CSV файл',
        help_text='CSV файл с колонками: username,fio,department_code'
    )

    def clean_file(self):
        """
        Проверяет формат и содержимое файла.

        Raises:
            ValidationError: Если файл имеет неверный формат

        Returns:
            File: Проверенный файл
        """
        file = self.cleaned_data['file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError('Файл должен быть в формате CSV')
        return file

    def process_file(self):
        """
        Обрабатывает загруженный CSV файл.

        Returns:
            tuple: (created_count, updated_count, errors)
                created_count (int): Количество созданных пользователей
                updated_count (int): Количество обновленных пользователей
                errors (list): Список ошибок при обработке
        """
        file = self.cleaned_data['file']
        created = 0
        updated = 0
        errors = []

        try:
            reader = csv.DictReader(
                TextIOWrapper(file, encoding='utf-8-sig')
            )
            for row in reader:
                try:
                    user, created = User.objects.update_or_create(
                        username=row['username'],
                        defaults={
                            'fio': row['fio'],
                            'department': Department.objects.get(
                                code=row['department_code']
                            )
                        }
                    )
                    if created:
                        created += 1
                    else:
                        updated += 1
                except Exception as e:
                    errors.append(f"Строка {reader.line_num}: {str(e)}")
        except Exception as e:
            errors.append(f"Ошибка обработки файла: {str(e)}")

        return created, updated, errors
```

## 🔌 API

### PrintEventViewSet (printing/api.py)
```python
class PrintEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с событиями печати через API.

    Attributes:
        queryset (QuerySet): Базовый QuerySet для выборки данных
        serializer_class (Serializer): Класс сериализатора
        permission_classes (list): Список классов разрешений
        filter_backends (list): Список бэкендов фильтрации
        filterset_fields (list): Поля для фильтрации

    Methods:
        get_queryset(): Возвращает отфильтрованный QuerySet
        perform_create(): Дополнительная логика при создании
        get_serializer_class(): Выбор сериализатора

    Example:
        Requests:
        GET /api/events/ - список всех событий
        POST /api/events/ - создание нового события
        GET /api/events/{id}/ - детали события
        PUT /api/events/{id}/ - обновление события
        DELETE /api/events/{id}/ - удаление события
    """
    queryset = PrintEvent.objects.all()
    serializer_class = PrintEventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'printer', 'timestamp']

    def get_queryset(self):
        """
        Возвращает QuerySet с учетом прав пользователя.

        Returns:
            QuerySet: Отфильтрованный список событий
        """
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(user=self.request.user) |
                Q(user__department=self.request.user.department)
            )
        return queryset.select_related('user', 'printer')

    def perform_create(self, serializer):
        """
        Дополнительная логика при создании события.

        Args:
            serializer (Serializer): Сериализатор с валидными данными
        """
        serializer.save(timestamp=timezone.now())

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия.

        Returns:
            Serializer: Класс сериализатора
        """
        if self.action in ['list', 'retrieve']:
            return PrintEventDetailSerializer
        return PrintEventSerializer
```

## 🔐 Аутентификация

### WindowsAuthBackend (accounts/backends.py)
```python
class WindowsAuthBackend:
    """
    Бэкенд аутентификации через Windows Active Directory.

    Methods:
        authenticate(): Аутентификация пользователя
        get_user(): Получение пользователя по ID
        get_user_groups(): Получение групп пользователя из AD

    Example:
        settings.py:
        AUTHENTICATION_BACKENDS = [
            'django.contrib.auth.backends.ModelBackend',
            'accounts.backends.WindowsAuthBackend',
        ]
    """

    def authenticate(self, request, username=None):
        """
        Аутентифицирует пользователя через Windows.

        Args:
            request (HttpRequest): HTTP запрос
            username (str): Имя пользователя Windows

        Returns:
            User: Объект пользователя или None
        """
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        """
        Получает пользователя по ID.

        Args:
            user_id (int): ID пользователя

        Returns:
            User: Объект пользователя или None
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def get_user_groups(self, username):
        """
        Получает группы пользователя из Active Directory.

        Args:
            username (str): Имя пользователя Windows

        Returns:
            list: Список групп пользователя
        """
        try:
            groups = win32security.GetTokenInformation(
                win32security.LogonUser(
                    username,
                    None,
                    None,
                    win32security.LOGON32_LOGON_INTERACTIVE,
                    win32security.LOGON32_PROVIDER_DEFAULT
                ),
                win32security.TokenGroups
            )
            return [g.GetName() for g in groups]
        except Exception:
            return []
```

## 📊 Сигналы

### printing/signals.py
```python
@receiver(post_save, sender=PrintEvent)
def update_statistics(sender, instance, created, **kwargs):
    """
    Обновляет статистику после создания события печати.

    Args:
        sender (Model): Модель, отправившая сигнал
        instance (PrintEvent): Экземпляр события печати
        created (bool): Флаг создания нового объекта
        **kwargs: Дополнительные аргументы

    Example:
        >>> event = PrintEvent.objects.create(...)
        # Сигнал автоматически вызовется после сохранения
    """
    if created:
        cache.delete(f'print_stats_{instance.user.department.id}')
        cache.delete('total_print_stats')
```

## 🧪 Тесты

### printing/tests/test_models.py
```python
class PrintEventTests(TestCase):
    """
    Тесты для модели PrintEvent.

    Methods:
        setUp(): Подготовка данных для тестов
        test_print_event_creation(): Тест создания события
        test_get_cost(): Тест расчета стоимости
        test_get_department(): Тест получения отдела

    Example:
        >>> python manage.py test printing.tests.test_models
    """

    def setUp(self):
        """Подготовка данных для тестов."""
        self.department = Department.objects.create(
            name='Test Department',
            code='TEST'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            department=self.department
        )
        self.printer = Printer.objects.create(
            name='Test Printer',
            cost_per_page=Decimal('2.00')
        )

    def test_print_event_creation(self):
        """Тест создания события печати."""
        event = PrintEvent.objects.create(
            user=self.user,
            printer=self.printer,
            pages=5,
            timestamp=timezone.now()
        )
        self.assertEqual(event.pages, 5)
        self.assertEqual(event.user, self.user)

    def test_get_cost(self):
        """Тест расчета стоимости печати."""
        event = PrintEvent.objects.create(
            user=self.user,
            printer=self.printer,
            pages=5,
            timestamp=timezone.now()
        )
        self.assertEqual(event.get_cost(), Decimal('10.00'))
```

## See Also

- [DEVELOPER_GUIDE](DEVELOPER_GUIDE.md) - соседняя страница раздела
- [README](README.md) - следующая страница раздела
- [Deployment](../deployment.md) - актуальные инструкции запуска
