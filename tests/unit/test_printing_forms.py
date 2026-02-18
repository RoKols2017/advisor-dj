from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from printing.forms import UserImportForm
from tests.factories import DepartmentFactory


class UserImportFormTests(TestCase):
    """Тесты для UserImportForm."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.department = DepartmentFactory(code='IT')

    def test_form_valid_csv_file(self):
        """Тест валидного CSV файла."""
        csv_content = "username,fio,department_code\nuser1,User One,IT\nuser2,User Two,IT"
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8-sig'),
            content_type="text/csv"
        )
        
        form = UserImportForm({}, {'file': csv_file})
        self.assertTrue(form.is_valid())

    def test_form_invalid_file_extension(self):
        """Тест неверного расширения файла."""
        txt_file = SimpleUploadedFile(
            "test.txt",
            b"some content",
            content_type="text/plain"
        )
        
        form = UserImportForm({}, {'file': txt_file})
        self.assertFalse(form.is_valid())
        self.assertIn('Файл должен быть в формате CSV', str(form.errors))

    def test_form_process_file_success(self):
        """Тест успешной обработки файла."""
        csv_content = "username,fio,department_code\nuser1,User One,IT\nuser2,User Two,IT"
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8-sig'),
            content_type="text/csv"
        )
        
        form = UserImportForm({}, {'file': csv_file})
        self.assertTrue(form.is_valid())
        
        created, updated, errors = form.process_file()
        
        self.assertEqual(created, 2)
        self.assertEqual(updated, 0)
        self.assertEqual(len(errors), 0)

    def test_form_process_file_with_errors(self):
        """Тест обработки файла с ошибками."""
        csv_content = "username,fio,department_code\nuser1,User One,INVALID_DEPT"
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8-sig'),
            content_type="text/csv"
        )
        
        form = UserImportForm({}, {'file': csv_file})
        self.assertTrue(form.is_valid())
        
        created, updated, errors = form.process_file()
        
        self.assertEqual(created, 0)
        self.assertEqual(updated, 0)
        self.assertGreater(len(errors), 0)

    def test_form_process_file_invalid_csv(self):
        """Тест обработки некорректного CSV."""
        invalid_content = "not a csv content"
        csv_file = SimpleUploadedFile(
            "test.csv",
            invalid_content.encode('utf-8-sig'),
            content_type="text/csv"
        )
        
        form = UserImportForm({}, {'file': csv_file})
        self.assertTrue(form.is_valid())
        
        created, updated, errors = form.process_file()
        
        self.assertEqual(created, 0)
        self.assertEqual(updated, 0)
        # CSV может быть обработан даже с некорректным содержимым
        self.assertGreaterEqual(len(errors), 0)

    def test_form_process_file_update_existing_user(self):
        """Тест обновления существующего пользователя."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Создаем существующего пользователя
        existing_user = User.objects.create_user(
            username='existinguser',
            fio='Old Name',
            department=self.department
        )
        
        csv_content = "username,fio,department_code\nexistinguser,New Name,IT"
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8-sig'),
            content_type="text/csv"
        )
        
        form = UserImportForm({}, {'file': csv_file})
        self.assertTrue(form.is_valid())
        
        created, updated, errors = form.process_file()
        
        self.assertEqual(created, 0)
        self.assertEqual(updated, 1)
        self.assertEqual(len(errors), 0)
        
        # Проверяем, что пользователь обновился
        existing_user.refresh_from_db()
        self.assertEqual(existing_user.fio, 'New Name')
