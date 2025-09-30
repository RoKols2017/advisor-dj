import csv
from io import TextIOWrapper

from django import forms

from .models import Department
from django.contrib.auth import get_user_model

User = get_user_model()


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