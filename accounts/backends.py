from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import win32security
import pywintypes

User = get_user_model()


class WindowsAuthBackend(ModelBackend):
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

    def authenticate(self, request, username=None, password=None):
        """
        Аутентифицирует пользователя через Windows.

        Args:
            request (HttpRequest): HTTP запрос
            username (str): Имя пользователя Windows

        Returns:
            User: Объект пользователя или None
        """
        try:
            # Пробуем получить токен Windows
            token = win32security.LogonUser(
                username,
                None,  # домен
                password,
                win32security.LOGON32_LOGON_NETWORK,
                win32security.LOGON32_PROVIDER_DEFAULT
            )

            if token:
                # Если аутентификация Windows успешна, получаем или создаем пользователя
                user, created = User.objects.get_or_create(
                    username=username.lower(),
                    defaults={
                        'is_active': True,
                    }
                )
                return user if user.is_active else None

        except pywintypes.error:
            return None

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