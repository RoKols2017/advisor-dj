from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class OrganizationalUnit(models.Model):
    """
    Модель для хранения организационных подразделений (OU) из Active Directory.
    """
    code = models.CharField('Код подразделения', max_length=20, unique=True)
    name = models.CharField('Название', max_length=255)
    distinguished_name = models.CharField('Distinguished Name', max_length=512, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительское подразделение'
    )
    created_at = models.DateTimeField('Дата создания', default=timezone.now)

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_path(self):
        """Возвращает полный путь подразделения, включая родительские"""
        path = [self]
        parent = self.parent
        while parent:
            path.append(parent)
            parent = parent.parent
        return ' / '.join(str(ou) for ou in reversed(path))


class User(AbstractUser):
    """
    Расширенная модель пользователя для работы с Active Directory.
    Используется как для аутентификации, так и для хранения информации о пользователях печати.

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
    # Стандартные поля из AbstractUser:
    # username - логин пользователя (из AD)
    # is_active - активен ли пользователь
    # date_joined - дата создания
    
    # Дополнительные поля для интеграции с AD
    fio = models.CharField('ФИО', max_length=255, blank=True)
    department = models.ForeignKey(
        'printing.Department',  # Используем строковое имя модели
        on_delete=models.PROTECT,
        null=True,
        related_name='users',
        verbose_name='Отдел'
    )

    class Meta(AbstractUser.Meta):
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.fio if self.fio else self.username

    def save(self, *args, **kwargs):
        # Если ФИО не заполнено, формируем его из first_name и last_name
        if not self.fio and (self.first_name or self.last_name):
            self.fio = f"{self.last_name} {self.first_name}".strip()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Полное имя пользователя"""
        if self.fio:
            return self.fio
        return f"{self.first_name} {self.last_name}".strip() or self.username