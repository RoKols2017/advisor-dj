import csv
from io import StringIO

from django import forms

from accounts.services import UserService
from printing.models import Department


class UserImportForm(forms.Form):
    """
    Форма для импорта пользователей из CSV файла.

    Fields:
        file (FileField): Поле для загрузки CSV файла

    Methods:
        clean_file(): Валидация файла

    Note:
        Для обработки файла используйте printing.services.import_users_from_csv_stream()

    Example:
        >>> form = UserImportForm(request.POST, request.FILES)
        >>> if form.is_valid():
        ...     from printing.services import import_users_from_csv_stream
        ...     result = import_users_from_csv_stream(form.cleaned_data['file'])
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

    def process_file(self) -> tuple[int, int, list[str]]:
        if not hasattr(self, 'cleaned_data') or 'file' not in self.cleaned_data:
            raise ValueError('Form must be validated before processing')

        uploaded = self.cleaned_data['file']
        uploaded.seek(0)

        try:
            content = uploaded.read().decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            return 0, 0, [f'Ошибка декодирования CSV: {exc}']

        reader = csv.DictReader(StringIO(content))
        required_columns = {'username', 'fio', 'department_code'}
        if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
            return 0, 0, [
                'Неверный формат CSV. Ожидаются колонки: username,fio,department_code'
            ]

        created = 0
        updated = 0
        errors: list[str] = []

        for row_index, row in enumerate(reader, start=2):
            username = (row.get('username') or '').strip()
            fio = (row.get('fio') or '').strip()
            department_code = (row.get('department_code') or '').strip()

            if not username or not department_code:
                errors.append(f'Строка {row_index}: username и department_code обязательны')
                continue

            department = Department.objects.filter(code__iexact=department_code).first()
            if not department:
                errors.append(f'Строка {row_index}: отдел не найден: {department_code}')
                continue

            user, was_created = UserService.create_or_update_user(
                username=username,
                fio=fio or username,
                department_code=department.code,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return created, updated, errors
