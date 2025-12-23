from django import forms


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
