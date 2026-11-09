"""
Пользовательские исключения приложения.
Стоматология «Улыбка» — Задание 4

Что такое исключения?
----------------------
Исключения — это специальные объекты, которые используются для обработки ошибок.

Зачем нужны пользовательские исключения?
-----------------------------------------
1. Они дают понятные названия ошибкам (UserNotFoundError вместо просто "Error")
2. Они позволяют обрабатывать разные ошибки по-разному
3. Они делают код более читаемым

Пример использования:
    try:
        user = find_user("admin")
    except UserNotFoundError:
        print("Пользователь не найден")
    except DatabaseError:
        print("Ошибка базы данных")

Иерархия исключений:
    AppException (базовое исключение приложения)
    ├── DatabaseError (ошибка базы данных)
    ├── AuthenticationError (ошибка авторизации)
    │   ├── UserNotFoundError (пользователь не найден)
    │   ├── IncorrectCredentialsError (неверный логин/пароль)
    │   └── UserBlockedError (пользователь заблокирован)
    ├── CaptchaError (ошибка капчи)
    │   └── CaptchaFailedError (капча не пройдена)
    ├── DuplicateLoginError (логин уже существует)
    └── PermissionError (нет прав доступа)
"""


class AppException(Exception):
    """
    Базовое исключение приложения.
    
    Все пользовательские исключения наследуются от этого класса.
    Это позволяет ловить все ошибки приложения одним except.
    
    Пример:
        try:
            do_something()
        except AppException:
            print("Произошла ошибка приложения")
    """
    pass  # "pass" означает "ничего не делать" — это заглушка


class DatabaseError(AppException):
    """
    Ошибка работы с базой данных.
    
    Возникает, когда происходит ошибка при работе с PostgreSQL:
    - Не удалось подключиться к базе
    - Ошибка выполнения SQL-запроса
    - Таблица не найдена
    """
    pass


class AuthenticationError(AppException):
    """
    Ошибка авторизации.
    
    Возникает, когда пользователь не может войти в систему:
    - Неверный логин или пароль
    - Пользователь заблокирован
    - Ошибка при проверке учётных данных
    """
    pass


class UserNotFoundError(AuthenticationError):
    """
    Пользователь не найден.
    
    Возникает, когда пользователь вводит логин, которого нет в базе данных.
    
    Пример:
        try:
            user = db_manager.check_user_exists("unknown_user")
            if not user:
                raise UserNotFoundError("unknown_user")
        except UserNotFoundError as e:
            print(f"Пользователь '{e.login}' не найден")
    """
    def __init__(self, login):
        """
        Конструктор исключения.
        
        Args:
            login — логин пользователя, который не найден
        """
        self.login = login  # Сохраняем логин для доступа к нему
        # Вызываем конструктор родительского класса (AuthenticationError)
        # super().__init__() — это способ вызвать метод родительского класса
        super().__init__(f"Пользователь '{login}' не найден")


class IncorrectCredentialsError(AuthenticationError):
    """
    Неверный логин или пароль.
    
    Возникает, когда пользователь вводит неправильный пароль.
    
    Пример:
        try:
            if password != correct_password:
                raise IncorrectCredentialsError(2)  # 2 — осталось попыток
        except IncorrectCredentialsError as e:
            print(f"Неверный пароль. Осталось попыток: {e.attempts_left}")
    """
    def __init__(self, attempts_left):
        """
        Конструктор исключения.
        
        Args:
            attempts_left — количество оставшихся попыток ввода пароля
        """
        self.attempts_left = attempts_left  # Сохраняем количество попыток
        super().__init__(f"Неверный логин или пароль. Осталось попыток: {attempts_left}")


class UserBlockedError(AuthenticationError):
    """
    Пользователь заблокирован.
    
    Возникает, когда пользователь пытается войти, но его учётная запись заблокирована.
    Блокировка происходит после 3 неверных попыток ввода пароля или капчи.
    
    Пример:
        try:
            user = authenticate("admin", "password")
        except UserBlockedError as e:
            print(f"Пользователь '{e.login}' заблокирован. Обратитесь к администратору")
    """
    def __init__(self, login):
        """
        Конструктор исключения.
        
        Args:
            login — логин заблокированного пользователя
        """
        self.login = login  # Сохраняем логин
        super().__init__("Вы заблокированы. Обратитесь к администратору")


class CaptchaError(AppException):
    """
    Ошибка капчи.
    
    Возникает, когда пользователь не может пройти проверку капчи.
    """
    pass


class CaptchaFailedError(CaptchaError):
    """
    Капча не пройдена.
    
    Возникает, когда пользователь неправильно собирает пазл.
    """
    def __init__(self, attempts_left):
        """
        Конструктор исключения.
        
        Args:
            attempts_left — количество оставшихся попыток собрать пазл
        """
        self.attempts_left = attempts_left
        super().__init__(f"Пазл собран неверно. Осталось попыток: {attempts_left}")


class DuplicateLoginError(AppException):
    """
    Логин уже существует.
    
    Возникает, когда администратор пытается добавить пользователя с логином,
    который уже есть в базе данных.
    
    Пример:
        try:
            db_manager.insert_user("admin", "password", "Администратор")
        except DuplicateLoginError as e:
            print(f"Пользователь с логином '{e.login}' уже существует")
    """
    def __init__(self, login):
        """
        Конструктор исключения.
        
        Args:
            login — логин, который уже существует
        """
        self.login = login
        super().__init__(f"Пользователь с логином '{login}' уже существует")


class PermissionError(AppException):
    """
    Ошибка прав доступа.
    
    Возникает, когда пользователь пытается выполнить действие,
    на которое у него нет прав.
    
    Пример:
        try:
            if user.role != "Администратор":
                raise PermissionError("Администратор")
        except PermissionError as e:
            print(f"Доступ разрешён только для роли: {e.required_role}")
    """
    def __init__(self, required_role):
        """
        Конструктор исключения.
        
        Args:
            required_role — роль, которая требуется для выполнения действия
        """
        self.required_role = required_role
        super().__init__(f"Доступ разрешён только для роли: {required_role}")
