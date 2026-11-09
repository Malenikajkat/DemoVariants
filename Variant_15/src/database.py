"""
Модуль работы с базой данных PostgreSQL.
Стоматология «Улыбка» — Задание 4

Этот модуль отвечает за:
- Подключение к базе данных PostgreSQL
- Выполнение SQL-запросов
- Получение данных из базы

Как работает:
1. При запуске приложения создаётся объект db_manager
2. При необходимости выполняется запрос к базе данных
3. Результаты запроса возвращаются в виде списка словарей

Пример использования:
    users = db_manager.fetch_all("SELECT * FROM user_account")
    # users будет списком: [{"id": 1, "login": "admin", ...}, ...]
"""

import sys          # Для работы с системными функциями
from pathlib import Path  # Для работы с путями к файлам

# Пытаемся импортировать psycopg2 — библиотеку для работы с PostgreSQL
try:
    import psycopg2  # Основная библиотека для подключения к PostgreSQL
    from psycopg2.extras import RealDictCursor  # Курсор, который возвращает данные как словари
except ImportError:
    # Если библиотека не установлена — показываем ошибку
    print("Ошибка: не установлен psycopg2-binary")
    print("Установите: pip install psycopg2-binary")
    sys.exit(1)  # Завершаем программу

from PyQt6.QtWidgets import QMessageBox  # Для показа окон с сообщениями

# Путь к корню проекта (папка, где лежит main.py)
PROJECT_ROOT = Path(__file__).parent.parent

# ==================== НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ ====================
# Здесь указываем параметры подключения к PostgreSQL
DB_CONFIG = {
    "host": "localhost",        # Адрес сервера базы данных (localhost = этот компьютер)
    "port": 5432,               # Порт PostgreSQL (по умолчанию 5432)
    "database": "stomatologiya", # Имя базы данных (должна быть создана заранее)
    "user": "postgres",         # Имя пользователя (по умолчанию postgres)
    "password": "12345"         # Пароль пользователя
}


class DatabaseManager:
    """
    Менеджер базы данных.
    
    Этот класс управляет подключением к PostgreSQL и выполнением запросов.
    
    Пример использования:
        db = DatabaseManager()
        db.connect()  # Подключаемся
        users = db.fetch_all("SELECT * FROM user_account")  # Получаем данные
        db.disconnect()  # Отключаемся
    """

    def __init__(self):
        """
        Конструктор класса.
        
        При создании объекта connection ещё не установлен.
        Подключение происходит при вызове метода connect().
        """
        self.connection = None  # Соединение с базой данных (пока None)

    def connect(self, parent_widget=None):
        """
        Устанавливает подключение к базе данных.
        
        Args:
            parent_widget — родительское окно (для показа сообщений об ошибках)
        
        Returns:
            True — если подключение успешно
            False — если произошла ошибка
        """
        try:
            # psycopg2.connect создаёт соединение с базой данных
            # DB_CONFIG — это словарь с параметрами подключения
            self.connection = psycopg2.connect(**DB_CONFIG)
            return True
        except psycopg2.OperationalError as e:
            # Если ошибка подключения — показываем сообщение
            print(f"\n!!! ОШИБКА ПОДКЛЮЧЕНИЯ К БД: {e}")
            print(f"   Проверьте:\n"
                  f"   1. Запущен ли PostgreSQL\n"
                  f"   2. Правильные ли параметры в database.py\n"
                  f"   3. Существует ли база 'stomatologiya'\n")
            
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Ошибка подключения к БД",
                    f"Не удалось подключиться к базе данных:\n{e}\n\n"
                    f"Проверьте:\n"
                    f"1. Запущен ли PostgreSQL\n"
                    f"2. Правильные ли параметры в database.py\n"
                    f"3. Существует ли база 'stomatologiya'"
                )
            return False

    def disconnect(self):
        """
        Закрывает подключение к базе данных.
        
        Важно вызывать этот метод при закрытии программы,
        чтобы освободить ресурсы.
        """
        # Проверяем, что соединение существует и не закрыто
        if self.connection and not self.connection.closed:
            self.connection.close()  # Закрываем соединение

    def execute(self, query, params=None):
        """
        Выполняет SQL-запрос без возврата данных.
        
        Используется для INSERT, UPDATE, DELETE запросов.
        
        Args:
            query — SQL-запрос (например: "INSERT INTO users (name) VALUES (%s)")
            params — параметры запроса (например: ("Иван",))
        
        Returns:
            True — если запрос выполнен успешно
            False — если произошла ошибка
        """
        # Проверяем, что соединение установлено
        if not self.connection or self.connection.closed:
            if not self.connect():  # Если нет — пытаемся подключиться
                return False
        
        try:
            # Создаём курсор — это объект для выполнения запросов
            cursor = self.connection.cursor()
            
            # Выполняем запрос
            # %s — это место, куда подставляются параметры
            # psycopg2 автоматически экранирует параметры (защита от SQL-инъекций)
            cursor.execute(query, params)
            
            # Фиксируем изменения (сохраняем в базу)
            self.connection.commit()
            
            # Закрываем курсор
            cursor.close()
            return True
        except Exception as e:
            # Если ошибка — отменяем изменения
            if self.connection:
                self.connection.rollback()
            raise e  # Повторно выбрасываем ошибку

    def fetch_one(self, query, params=None):
        """
        Выполняет SQL-запрос и возвращает одну запись.
        
        Используется для SELECT запросов, когда нужна одна запись.
        
        Args:
            query — SQL-запрос (например: "SELECT * FROM users WHERE id = %s")
            params — параметры запроса
        
        Returns:
            Словарь с данными (например: {"id": 1, "login": "admin"})
            или None, если запись не найдена
        """
        # Проверяем соединение
        if not self.connection or self.connection.closed:
            if not self.connect():
                return None
        
        try:
            # Создаём курсор с RealDictCursor
            # RealDictCursor возвращает данные как словари, а не как кортежи
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Выполняем запрос
            cursor.execute(query, params)
            
            # Получаем одну запись
            result = cursor.fetchone()
            
            # Закрываем курсор
            cursor.close()
            return result
        except Exception as e:
            raise e

    def fetch_all(self, query, params=None):
        """
        Выполняет SQL-запрос и возвращает все записи.
        
        Используется для SELECT запросов, когда нужна таблица.
        
        Args:
            query — SQL-запрос (например: "SELECT * FROM users")
            params — параметры запроса
        
        Returns:
            Список словарей (например: [{"id": 1, "login": "admin"}, ...])
            или пустой список, если записей нет
        """
        # Проверяем соединение
        if not self.connection or self.connection.closed:
            if not self.connect():
                return []
        
        try:
            # Создаём курсор с RealDictCursor
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Выполняем запрос
            cursor.execute(query, params)
            
            # Получаем все записи
            results = cursor.fetchall()
            
            # Закрываем курсор
            cursor.close()
            return results
        except Exception as e:
            raise e

    def check_user_exists(self, login):
        """
        Проверяет существование пользователя по логину.
        
        Args:
            login — логин пользователя (например: "admin")
        
        Returns:
            Словарь с данными пользователя, если найден
            или None, если не найден
        """
        # SQL-запрос: выбираем все поля из user_account, где login = %s
        # %s — это место для параметра (защита от SQL-инъекций)
        query = "SELECT id, login, password_hash, role, is_blocked, created_at FROM user_account WHERE login = %s"
        return self.fetch_one(query, (login,))  # (login,) — это кортеж с одним элементом

    def get_all_users(self):
        """
        Возвращает всех пользователей.
        
        Returns:
            Список словарей с данными пользователей
        """
        query = """
            SELECT id, login, role, is_blocked, created_at 
            FROM user_account 
            ORDER BY id
        """
        return self.fetch_all(query)

    def insert_user(self, login, password_hash, role):
        """
        Добавляет нового пользователя в базу данных.
        
        Args:
            login — логин пользователя
            password_hash — хеш пароля (или пароль в открытом виде для простоты)
            role — роль пользователя ("Администратор" или "Пользователь")
        
        Returns:
            ID нового пользователя или None, если ошибка
        """
        query = """
            INSERT INTO user_account (login, password_hash, role, is_blocked)
            VALUES (%s, %s, %s, FALSE)
            RETURNING id
        """
        result = self.fetch_one(query, (login, password_hash, role))
        return result["id"] if result else None

    def update_user(self, user_id, login=None, password_hash=None, role=None, is_blocked=None):
        """
        Обновляет данные пользователя.
        
        Args:
            user_id — ID пользователя
            login — новый логин (или None, если не меняем)
            password_hash — новый пароль (или None, если не меняем)
            role — новая роль (или None, если не меняем)
            is_blocked — флаг блокировки (или None, если не меняем)
        
        Returns:
            True — если обновление успешно
            False — если ошибка
        """
        updates = []  # Список полей для обновления
        params = []   # Список параметров
        
        # Добавляем поля, которые нужно обновить
        if login is not None:
            updates.append("login = %s")
            params.append(login)
        if password_hash is not None:
            updates.append("password_hash = %s")
            params.append(password_hash)
        if role is not None:
            updates.append("role = %s")
            params.append(role)
        if is_blocked is not None:
            updates.append("is_blocked = %s")
            params.append(is_blocked)
        
        # Если ничего не нужно обновлять — возвращаем False
        if not updates:
            return False
        
        # Добавляем ID пользователя в конец параметров
        params.append(user_id)
        
        # Формируем SQL-запрос
        # UPDATE user_account SET login = %s, role = %s WHERE id = %s
        query = f"UPDATE user_account SET {', '.join(updates)} WHERE id = %s"
        return self.execute(query, tuple(params))

    def delete_user(self, user_id):
        """
        Удаляет пользователя из базы данных.
        
        Args:
            user_id — ID пользователя
        
        Returns:
            True — если удаление успешно
            False — если ошибка
        """
        query = "DELETE FROM user_account WHERE id = %s"
        return self.execute(query, (user_id,))

    def get_orders(self):
        """
        Возвращает все заказы покупателей.
        
        Returns:
            Список словарей с данными заказов
        """
        query = """
            SELECT id, order_number, order_date, customer_id, executor
            FROM customer_order
            ORDER BY id
        """
        return self.fetch_all(query)

    def get_products(self):
        """
        Возвращает всю продукцию.
        
        Returns:
            Список словарей с данными продукции
        """
        query = "SELECT code, name FROM product ORDER BY code"
        return self.fetch_all(query)


# ==================== ГЛОБАЛЬНЫЙ МЕНЕДЖЕР БАЗЫ ДАННЫХ ====================
# Создаём объект db_manager, который будет использоваться во всём приложении
# Это "одиночка" — один экземпляр на всё приложение
db_manager = DatabaseManager()
