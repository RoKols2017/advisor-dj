from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.services import UserService
from printing.models import Department

User = get_user_model()


class UserServiceTests(TestCase):
    """Тесты для UserService."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.department = Department.objects.create(
            code='IT',
            name='IT Department'
        )

    def test_create_or_update_user_new_user(self):
        """Тест создания нового пользователя."""
        user, created = UserService.create_or_update_user(
            username='newuser',
            fio='New User',
            department_code='IT'
        )
        
        self.assertTrue(created)
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.fio, 'New User')
        self.assertEqual(user.department.code, 'IT')

    def test_create_or_update_user_existing_user(self):
        """Тест обновления существующего пользователя."""
        # Создаем пользователя
        user, created = UserService.create_or_update_user(
            username='existinguser',
            fio='Old Name',
            department_code='IT'
        )
        self.assertTrue(created)
        
        # Обновляем пользователя
        updated_user, created = UserService.create_or_update_user(
            username='existinguser',
            fio='New Name',
            department_code='IT'
        )
        
        self.assertFalse(created)
        self.assertEqual(updated_user.id, user.id)
        self.assertEqual(updated_user.fio, 'New Name')

    def test_create_or_update_user_new_department(self):
        """Тест создания пользователя с новым отделом."""
        user, created = UserService.create_or_update_user(
            username='user_with_new_dept',
            fio='User With New Dept',
            department_code='HR'
        )
        
        self.assertTrue(created)
        self.assertEqual(user.department.code, 'HR')
        self.assertTrue(Department.objects.filter(code='HR').exists())

    def test_get_user_by_username_existing(self):
        """Тест получения существующего пользователя."""
        user = User.objects.create_user(
            username='testuser',
            fio='Test User',
            department=self.department
        )
        
        found_user = UserService.get_user_by_username('testuser')
        self.assertEqual(found_user, user)

    def test_get_user_by_username_nonexistent(self):
        """Тест получения несуществующего пользователя."""
        found_user = UserService.get_user_by_username('nonexistent')
        self.assertIsNone(found_user)

    def test_get_user_by_username_case_insensitive(self):
        """Тест поиска пользователя без учета регистра."""
        user = User.objects.create_user(
            username='TestUser',
            fio='Test User',
            department=self.department
        )
        
        found_user = UserService.get_user_by_username('testuser')
        self.assertEqual(found_user, user)
