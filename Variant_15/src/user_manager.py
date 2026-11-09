"""
Модуль управления пользователями.
Стоматология «Улыбка» — Задание 4

Этот модуль отвечает за:
- Добавление новых пользователей
- Редактирование данных пользователей
- Снятие блокировки с пользователей
- Удаление пользователей
- Проверку уникальности логина
- Загрузку таблицы пользователей в интерфейс

Как использовать:
    user_manager = UserManager(parent_window)
    user_manager.add_user("newuser", "password123", "Пользователь")
    user_manager.load_users_table(table_widget)
"""

# Импортируем QMessageBox для показа окон с сообщениями
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
# Импортируем Qt для работы с цветами
from PyQt6.QtCore import Qt

# Импортируем db_manager — объект для работы с базой данных
from Variant_15.src.database import db_manager


class UserManager:
    """
    Модуль управления пользователями (для администратора).
    
    Этот класс предоставляет методы для управления пользователями:
    - add_user() — добавить пользователя
    - edit_user() — редактировать пользователя
    - unblock_user() — снять блокировку
    - delete_user() — удалить пользователя
    - load_users_table() — загрузить таблицу в интерфейс
    
    Пример использования:
        manager = UserManager(self)  # self — это родительское окно
        manager.add_user("ivan", "pass123", "Пользователь")
        manager.load_users_table(tbl_users)
    """

    def __init__(self, parent=None):
        """
        Конструктор класса.
        
        Args:
            parent — родительское окно (нужно для показа сообщений)
        """
        self.parent = parent  # Сохраняем ссылку на родительское окно

    def add_user(self, login, password, role):
        """
        Добавляет нового пользователя в базу данных.
        
        Эта функция:
        1. Проверяет, не занят ли уже такой логин
        2. Если логин свободен — добавляет пользователя
        3. Если логин занят — показывает ошибку
        
        Args:
            login — логин нового пользователя (например: "ivan")
            password — пароль нового пользователя (например: "pass123")
            role — роль пользователя ("Администратор" или "Пользователь")
        
        Returns:
            True — если пользователь добавлен
            False — если произошла ошибка
        """
        # Проверяем, не занят ли уже такой логин
        # db_manager.check_user_exists() возвращает пользователя, если найден
        existing = db_manager.check_user_exists(login)
        if existing:
            # Логин уже существует — показываем ошибку
            QMessageBox.warning(
                self.parent,
                "Ошибка",
                f"Пользователь с логином '{login}' уже существует"
            )
            return False

        try:
            # Добавляем пользователя в базу данных
            # db_manager.insert_user() возвращает ID нового пользователя
            user_id = db_manager.insert_user(login, password, role)
            
            # Показываем сообщение об успехе
            QMessageBox.information(
                self.parent,
                "Успех",
                f"Пользователь '{login}' успешно добавлен"
            )
            return user_id is not None
        except Exception as e:
            # Если произошла ошибка — показываем сообщение
            QMessageBox.critical(
                self.parent,
                "Ошибка",
                f"Не удалось добавить пользователя:\n{e}"
            )
            return False

    def edit_user(self, user_id, login, password, role):
        """
        Редактирует данные пользователя.
        
        Эта функция:
        1. Проверяет, не занят ли уже новый логин
        2. Если логин свободен — обновляет данные пользователя
        
        Args:
            user_id — ID пользователя, которого нужно редактировать
            login — новый логин
            password — новый пароль
            role — новая роль
        
        Returns:
            True — если пользователь обновлён
            False — если произошла ошибка
        """
        # Проверяем уникальность нового логина
        existing = db_manager.check_user_exists(login)
        # Если логин занят кем-то другим — показываем ошибку
        if existing and existing["id"] != user_id:
            QMessageBox.warning(
                self.parent,
                "Ошибка",
                f"Пользователь с логином '{login}' уже существует"
            )
            return False

        try:
            # Обновляем данные пользователя
            db_manager.update_user(
                user_id,
                login=login,
                password_hash=password,
                role=role
            )
            # Показываем сообщение об успехе
            QMessageBox.information(
                self.parent,
                "Успех",
                "Данные пользователя обновлены"
            )
            return True
        except Exception as e:
            # Если произошла ошибка — показываем сообщение
            QMessageBox.critical(
                self.parent,
                "Ошибка",
                f"Не удалось обновить данные:\n{e}"
            )
            return False

    def unblock_user(self, user_id, login):
        """
        Снимает блокировку с пользователя.
        
        Эта функция устанавливает is_blocked = FALSE в базе данных.
        
        Args:
            user_id — ID пользователя
            login — логин пользователя (для сообщения)
        
        Returns:
            True — если блокировка снята
            False — если произошла ошибка
        """
        try:
            # Обновляем пользователя: is_blocked = FALSE
            db_manager.update_user(user_id, is_blocked=False)
            # Показываем сообщение об успехе
            QMessageBox.information(
                self.parent,
                "Успех",
                f"Блокировка снята для пользователя '{login}'"
            )
            return True
        except Exception as e:
            # Если произошла ошибка — показываем сообщение
            QMessageBox.critical(
                self.parent,
                "Ошибка",
                f"Не удалось снять блокировку:\n{e}"
            )
            return False

    def delete_user(self, user_id, login):
        """
        Удаляет пользователя из базы данных.
        
        Эта функция сначала показывает диалог подтверждения,
        чтобы случайно не удалить пользователя.
        
        Args:
            user_id — ID пользователя
            login — логин пользователя (для сообщения)
        
        Returns:
            True — если пользователь удалён
            False — если пользователь отменил удаление или произошла ошибка
        """
        # Показываем диалог подтверждения
        # QMessageBox.question — это окно с вопросом (Да/Нет)
        reply = QMessageBox.question(
            self.parent,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить пользователя '{login}'?\n\n"
            "Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # По умолчанию выбираем "Нет"
        )

        # Если пользователь нажал "Да" — удаляем
        if reply != QMessageBox.StandardButton.Yes:
            return False

        try:
            # Удаляем пользователя из базы данных
            db_manager.delete_user(user_id)
            # Показываем сообщение об успехе
            QMessageBox.information(
                self.parent,
                "Успех",
                f"Пользователь '{login}' удалён"
            )
            return True
        except Exception as e:
            # Если произошла ошибка — показываем сообщение
            QMessageBox.critical(
                self.parent,
                "Ошибка",
                f"Не удалось удалить пользователя:\n{e}"
            )
            return False

    def load_users_table(self, table_widget):
        """
        Загружает данные пользователей в таблицу интерфейса.
        
        Эта функция:
        1. Получает всех пользователей из базы данных
        2. Создаёт строки в таблице
        3. Заполняет ячейки данными (ID, логин, роль, блокировка, дата создания)
        
        Args:
            table_widget — объект QTableWidget (таблица из интерфейса)
        
        Пример:
            manager = UserManager(self)
            manager.load_users_table(tbl_users)  # tbl_users — это таблица из UI
        """
        try:
            # Получаем всех пользователей из базы данных
            users = db_manager.get_all_users()
            
            # Устанавливаем количество строк в таблице
            table_widget.setRowCount(len(users))

            # Заполняем каждую строку данными
            for row, user in enumerate(users):
                # Записываем ID пользователя
                table_widget.setItem(row, 0, QTableWidgetItem(str(user["id"])))
                
                # Записываем логин
                table_widget.setItem(row, 1, QTableWidgetItem(user["login"]))
                
                # Записываем роль
                table_widget.setItem(row, 2, QTableWidgetItem(user["role"]))

                # Записываем флаг блокировки ("Да" или "Нет")
                blocked_text = "Да" if user["is_blocked"] else "Нет"
                item = QTableWidgetItem(blocked_text)
                
                # Если пользователь заблокирован — красим текст в красный цвет
                if user["is_blocked"]:
                    item.setForeground(Qt.GlobalColor.red)
                table_widget.setItem(row, 3, item)

                # Записываем дату создания (первые 19 символов: "2024-01-01 10:00:00")
                created = str(user["created_at"])[:19] if user["created_at"] else "-"
                table_widget.setItem(row, 4, QTableWidgetItem(created))

                # Добавляем иконку (🔓 если заблокирован, ✅ если нет)
                btn_unblock = QTableWidgetItem("🔓" if user["is_blocked"] else "✅")
                # Делаем ячейку некликабельной (только для отображения)
                btn_unblock.setFlags(Qt.ItemFlag.NoItemFlags)
                table_widget.setItem(row, 5, btn_unblock)

        except Exception as e:
            # Если произошла ошибка — показываем сообщение
            QMessageBox.critical(
                self.parent,
                "Ошибка",
                f"Не удалось загрузить список пользователей:\n{e}"
            )
