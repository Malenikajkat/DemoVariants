"""
Модуль авторизации.
Стоматология «Улыбка» — Задание 4

Этот модуль отвечает за:
- Проверку логина и пароля
- Блокировку учётной записи после нескольких неудачных попыток
- Отслеживание количества ошибок
- Показ сообщений об ошибках

Как работает авторизация:
1. Пользователь вводит логин и пароль
2. Программа проверяет, существует ли пользователь в базе
3. Если пользователь существует — проверяет пароль
4. Если пароль неверный — увеличивает счётчик ошибок
5. Если ошибок 3 и более — блокирует пользователя
6. Если всё правильно — разрешает вход

Безопасность:
- После 3 неверных попыток ввода пароля — пользователь блокируется
- После 3 неверных попыток сборки капчи — пользователь блокируется
- Блокировка сохраняется в базе данных (is_blocked = TRUE)
"""

# Импортируем db_manager — объект для работы с базой данных
from Variant_15.src.database import db_manager
# Импортируем классы исключений для обработки ошибок
from Variant_15.src.exceptions import (
    UserNotFoundError,      # Исключение: пользователь не найден
    IncorrectCredentialsError,  # Исключение: неверный логин/пароль
    UserBlockedError,       # Исключение: пользователь заблокирован
    AuthenticationError     # Исключение: ошибка авторизации
)
# Импортируем QMessageBox для показа окон с сообщениями
from PyQt6.QtWidgets import QMessageBox


class AuthModule:
    """
    Модуль авторизации пользователей.
    
    Этот класс отвечает за проверку логина и пароля.
    
    Пример использования:
        auth = AuthModule()
        try:
            user = auth.authenticate("admin", "admin123", captcha_solved=True)
            print(f"Добро пожаловать, {user['login']}!")
        except UserNotFoundError:
            print("Пользователь не найден")
        except UserBlockedError:
            print("Пользователь заблокирован")
    """

    # Максимальное количество попыток ввода пароля
    MAX_PASSWORD_ATTEMPTS = 3
    
    # Максимальное количество попыток сборки капчи
    MAX_CAPTCHA_ATTEMPTS = 3

    def __init__(self):
        """
        Конструктор класса.
        
        Создаём словари для отслеживания неудачных попыток:
        - failed_password_attempts — счётчик ошибок пароля по логину
        - failed_captcha_attempts — счётчик ошибок капчи по логину
        
        Пример:
            self.failed_password_attempts = {"admin": 2, "user1": 1}
        """
        self.failed_password_attempts = {}  # Словарь: login -> count
        self.failed_captcha_attempts = {}   # Словарь: login -> count

    def authenticate(self, login, password_hash, captcha_solved=False):
        """
        Выполняет авторизацию пользователя.
        
        Это главная функция авторизации. Она:
        1. Проверяет, существует ли пользователь
        2. Проверяет, не заблокирован ли пользователь
        3. Проверяет капчу (пазл)
        4. Проверяет пароль
        5. Если всё правильно — возвращает данные пользователя
        
        Args:
            login — логин пользователя (например: "admin")
            password_hash — пароль пользователя (в хешированном виде)
            captcha_solved — True, если капча пройдена успешно
        
        Returns:
            Словарь с данными пользователя:
            {
                "id": 1,
                "login": "admin",
                "password_hash": "admin123",
                "role": "Администратор",
                "is_blocked": False,
                "created_at": "2024-01-01 10:00:00"
            }
        
        Raises:
            UserNotFoundError — если пользователь не найден
            UserBlockedError — если пользователь заблокирован
            IncorrectCredentialsError — если неверный логин или пароль
        """
        try:
            # Проверяем существование пользователя в базе данных
            # db_manager.check_user_exists() возвращает словарь с данными пользователя
            # или None, если пользователь не найден
            user = db_manager.check_user_exists(login)

            # Если пользователь не найден — выбрасываем исключение
            if not user:
                raise UserNotFoundError(login)

            # Проверяем, не заблокирован ли пользователь
            # user["is_blocked"] — это True, если пользователь заблокирован
            if user["is_blocked"]:
                raise UserBlockedError(login)

            # Проверяем капчу (пазл)
            # Если капча не пройдена — это считается как ошибка
            if not captcha_solved:
                self._track_captcha_failure(login)  # Отмечаем неудачную попытку
                # Вычисляем, сколько попыток осталось
                captcha_left = self.MAX_CAPTCHA_ATTEMPTS - self.failed_captcha_attempts.get(login, 0)
                raise IncorrectCredentialsError(captcha_left)

            # Проверяем пароль
            # user["password_hash"] — это сохранённый пароль в базе
            if user["password_hash"] != password_hash:
                self._track_password_failure(login)  # Отмечаем неудачную попытку
                # Вычисляем, сколько попыток осталось
                attempts_left = self.MAX_PASSWORD_ATTEMPTS - self.failed_password_attempts.get(login, 0)
                raise IncorrectCredentialsError(attempts_left)

            # Если всё правильно — сбрасываем счётчики ошибок
            # (пользователь успешно вошёл, ошибки больше не актуальны)
            self._reset_attempts(login)

            # Возвращаем данные пользователя
            return dict(user)

        # Обработка исключений
        except (UserNotFoundError, UserBlockedError, IncorrectCredentialsError):
            # Перевыбрасываем эти исключения (не обрабатываем здесь)
            raise
        except Exception as e:
            # Если произошла другая ошибка — выбрасываем AuthenticationError
            raise AuthenticationError(f"Ошибка при авторизации: {e}")

    def _track_password_failure(self, login):
        """
        Отслеживает неудачную попытку ввода пароля.
        
        Эта функция вызывается, когда пользователь вводит неверный пароль.
        Она:
        1. Увеличивает счётчик ошибок для этого логина
        2. Если ошибок 3 и более — блокирует пользователя
        
        Args:
            login — логин пользователя, который ввёл неверный пароль
        """
        # Получаем текущий счётчик ошибок (по умолчанию 0)
        # self.failed_password_attempts.get(login, 0) — возвращает 0, если логин не найден
        self.failed_password_attempts[login] = self.failed_password_attempts.get(login, 0) + 1

        # Если ошибок 3 и более — блокируем пользователя
        if self.failed_password_attempts[login] >= self.MAX_PASSWORD_ATTEMPTS:
            # Обновляем пользователя в базе данных: устанавливаем is_blocked = TRUE
            db_manager.execute(
                "UPDATE user_account SET is_blocked = TRUE WHERE login = %s",
                (login,)  # (login,) — это кортеж с одним элементом
            )

    def _track_captcha_failure(self, login):
        """
        Отслеживает неудачную попытку сборки капчи.
        
        Эта функция вызывается, когда пользователь неправильно собирает пазл.
        Она работает так же, как _track_password_failure.
        
        Args:
            login — логин пользователя, который неправильно собрал пазл
        """
        # Увеличиваем счётчик ошибок капчи
        self.failed_captcha_attempts[login] = self.failed_captcha_attempts.get(login, 0) + 1

        # Если ошибок 3 и более — блокируем пользователя
        if self.failed_captcha_attempts[login] >= self.MAX_CAPTCHA_ATTEMPTS:
            # Обновляем пользователя в базе данных
            db_manager.execute(
                "UPDATE user_account SET is_blocked = TRUE WHERE login = %s",
                (login,)
            )

    def _reset_attempts(self, login):
        """
        Сбрасывает счётчики неудачных попыток.
        
        Эта функция вызывается, когда пользователь успешно авторизуется.
        Она обнуляет счётчики ошибок для этого логина.
        
        Args:
            login — логин пользователя, который успешно вошёл
        """
        self.failed_password_attempts[login] = 0  # Сбрасываем счётчик паролей
        self.failed_captcha_attempts[login] = 0   # Сбрасываем счётчик капчи

    def show_auth_message(self, parent, error):
        """
        Показывает сообщение об ошибке авторизации.
        
        Эта функция показывает разные сообщения в зависимости от типа ошибки:
        - UserNotFoundError — "Вы ввели неверный логин или пароль..."
        - UserBlockedError — "Вы заблокированы. Обратитесь к администратору"
        - IncorrectCredentialsError — "Вы ввели неверный логин или пароль..."
        
        Args:
            parent — родительское окно (для позиционирования сообщения)
            error — объект исключения (ошибки)
        """
        # Проверяем тип ошибки
        if isinstance(error, UserNotFoundError):
            # Пользователь не найден
            QMessageBox.critical(
                parent,
                "Ошибка авторизации",
                "Вы ввели неверный логин или пароль. Пожалуйста, проверьте ещё раз введённые данные"
            )
        elif isinstance(error, UserBlockedError):
            # Пользователь заблокирован
            QMessageBox.warning(
                parent,
                "Учётная запись заблокирована",
                "Вы заблокированы. Обратитесь к администратору"
            )
        elif isinstance(error, IncorrectCredentialsError):
            # Неверный логин или пароль
            QMessageBox.critical(
                parent,
                "Ошибка авторизации",
                "Вы ввели неверный логин или пароль. Пожалуйста, проверьте ещё раз введённые данные"
            )
        else:
            # Какая-то другая ошибка
            QMessageBox.critical(
                parent,
                "Ошибка",
                f"Произошла ошибка: {error}"
            )

    def show_success_message(self, parent):
        """
        Показывает сообщение об успешной авторизации.
        
        Args:
            parent — родительское окно (для позиционирования сообщения)
        """
        QMessageBox.information(
            parent,
            "Авторизация успешна",
            "Вы успешно авторизовались"
        )
