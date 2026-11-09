"""
Точка входа приложения.
Стоматология «Улыбка» — Задание 4

Этот файл запускает всё приложение. Он создаёт главное окно и запускает цикл обработки событий.

Архитектура приложения:
- PyQt6 — библиотека для создания графического интерфейса (GUI)
- Qt Designer — инструмент для визуального проектирования окон (.ui файлы)
- PostgreSQL — база данных для хранения информации
- psycopg2 — библиотека для работы с PostgreSQL из Python

Как работает приложение:
1. При запуске создаётся объект QApplication (это "движок" приложения)
2. Загружается окно авторизации из login_window.ui
3. Пользователь вводит логин/пароль и собирает пазл
4. После успешной авторизации открывается панель администратора или пользователя
5. Приложение работает, пока пользователь не выйдет
"""

import sys          # Модуль для работы с системными функциями (выход из программы)
import os           # Модуль для работы с файловой системой (путь к файлам)
from pathlib import Path  # Модуль для работы с путями (современный способ)

# ==================== ПРОВЕРКА ЗАВИСИМОСТЕЙ ====================
# Эта функция проверяет, установлены ли нужные библиотеки
# Если библиотека не установлена — программа покажет ошибку и закроется
def check_dependencies():
    """
    Проверяет наличие необходимых библиотек.
    
    Почему это важно:
    - PyQt6 нужна для графического интерфейса
    - psycopg2 нужна для работы с базой данных PostgreSQL
    
    Если вы видите ошибку "No module named PyQt6", значит библиотека не установлена.
    Чтобы установить: pip install PyQt6 psycopg2-binary
    """
    missing = []  # Список пустых библиотек
    for lib in ["PyQt6", "psycopg2"]:  # Проверяем каждую библиотеку
        try:
            # __import__(lib) пытается "импортировать" библиотеку
            # Если библиотека не найдена — возникнет ошибка ImportError
            __import__(lib)
        except ImportError:
            # Если библиотека не найдена, добавляем её в список
            missing.append(lib)
    
    # Если есть отсутствующие библиотеки — показываем ошибку
    if missing:
        # f-строка — это способ вставить переменные в строку
        # {', '.join(missing)} превращает список ['PyQt6', 'psycopg2'] в строку "PyQt6, psycopg2"
        print(f"Ошибка: не установлены библиотеки: {', '.join(missing)}")
        print(f"Установите: pip install {' '.join(missing)}")
        sys.exit(1)  # Завершаем программу с кодом ошибки 1

# Вызываем функцию проверки (это выполняется сразу при запуске файла)
check_dependencies()

# ==================== НАСТРОЙКА ПУТЕЙ ====================
# Получаем путь к папке проекта (корневая папка, где лежит main.py)
# __file__ — это путь к текущему файлу (main.py)
# .parent — это родительская папка (src/)
# .parent.parent — это папка проекта (proba/)
PROJECT_ROOT = Path(__file__).parent.parent

# Добавляем корень проекта в sys.path
# sys.path — это список папок, где Python ищет импортируемые модули
# Если мы не добавим корень проекта, то не сможем импортировать модули из src/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ==================== ИМПОРТ БИБЛИОТЕК ====================
# PyQt6.QtWidgets — это классы для создания элементов интерфейса
# QApplication — "движок" приложения (создаёт главный цикл событий)
# QMainWindow — основное окно приложения (с меню, тулбарами, статусбаром)
# QMessageBox — окна с сообщениями (ошибки, предупреждения, информация)
# QTableWidgetItem — элемент для таблицы (ячейка)
# QDialog — диалоговое окно (всплывающее окно для ввода данных)
# QVBoxLayout, QFormLayout — layouts (расположение элементов на окне)
# QLineEdit — поле для ввода текста
# QComboBox — выпадающий список
# QDialogButtonBox — кнопки "OK", "Cancel"
# QLabel — текстовая метка
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QDialog, QVBoxLayout,
    QLineEdit, QComboBox, QDialogButtonBox, QLabel
)

# PyQt6.QtGui — это классы для работы с графикой
# QFont — шрифт (название, размер)
from PyQt6.QtGui import QFont

# ==================== ИМПОРТ МОДУЛЕЙ ПРОЕКТА ====================
# Импортируем наши модули из папки src/
# from src.database import db_manager — импортируем объект db_manager из модуля database
# from src.auth_module import AuthModule — импортируем класс AuthModule
# from src.captcha_module import CaptchaWidget — импортируем класс CaptchaWidget
# from src.user_manager import UserManager — импортируем класс UserManager
# from src.exceptions import ... — импортируем классы исключений
from Variant_15.src.database import db_manager
from Variant_15.src.auth_module import AuthModule
from Variant_15.src.captcha_module import CaptchaWidget
from Variant_15.src.user_manager import UserManager
from Variant_15.src.exceptions import (
    UserNotFoundError,      # Исключение: пользователь не найден
    IncorrectCredentialsError,  # Исключение: неверный логин/пароль
    UserBlockedError,       # Исключение: пользователь заблокирован
    AuthenticationError     # Исключение: ошибка авторизации
)

# PyQt6.uic — модуль для загрузки .ui файлов (созданных в Qt Designer)
import PyQt6.uic as uic


# ==================== ОКНО АВТОРИЗАЦИИ ====================
# QMainWindow — это базовый класс для главного окна приложения
# LoginWindow наследуется от QMainWindow, то есть "является" окном
class LoginWindow(QMainWindow):
    """
    Окно авторизации с капчей.
    
    Это окно появляется при запуске программы.
    Пользователь должен:
    1. Ввести логин
    2. Ввести пароль
    3. Собрать пазл (капча)
    4. Нажать кнопку "Войти"
    
    Если всё правильно — откроется панель администратора или пользователя.
    """

    def __init__(self):
        """
        Конструктор класса — выполняется при создании объекта.
        
        Что происходит здесь:
        1. Вызываем super().__init__() — это инициализирует родительский класс (QMainWindow)
        2. Создаём объект AuthModule — модуль для проверки логина/пароля
        3. Загружаем .ui файл — это визуальное описание окна (сделано в Qt Designer)
        4. Подключаем кнопку "Войти" к функции _on_login
        5. Применяем стили (CSS)
        """
        super().__init__()  # Инициализируем родительский класс (QMainWindow)
        self.auth_module = AuthModule()  # Создаём модуль авторизации

        # Загружаем .ui файл из папки ui/
        # os.path.join — это способ соединить части пути в один путь
        # Например: "src" + "ui" + "login_window.ui" = "src/ui/login_window.ui"
        ui_path = os.path.join(PROJECT_ROOT, "ui", "login_window.ui")
        
        # uic.loadUi загружает .ui файл и создаёт в нём все элементы интерфейса
        # self — это ссылка на текущий объект (окно LoginWindow)
        # После загрузки все элементы из .ui файла станут атрибутами self
        # Например: self.login_field, self.password_field, self.login_button
        uic.loadUi(ui_path, self)

        # Подключаем кнопку "Войти" к функции _on_login
        # .clicked.connect — это сигнал (event) — когда кнопка нажата, вызывается функция
        self.login_button.clicked.connect(self._on_login)

        # Применяем стили из файла main.qss
        self._apply_styles()

    def _apply_styles(self):
        """
        Применяет CSS-стили к окну.
        
        Стили делают окно красивым (цвета, шрифты, отступы).
        Стили хранятся в файле resources/styles/main.qss
        """
        style_path = os.path.join(PROJECT_ROOT, "resources", "styles", "main.qss")
        if os.path.exists(style_path):  # Проверяем, существует ли файл стилей
            # Открываем файл и читаем его содержимое
            with open(style_path, "r", encoding="utf-8") as f:
                # setStyleSheet применяет стили ко всему окну
                self.setStyleSheet(f.read())

    def _on_login(self):
        """
        Обработчик нажатия кнопки «Войти».
        
        Эта функция вызывается, когда пользователь нажимает кнопку "Войти".
        Она:
        1. Получает логин и пароль из полей ввода
        2. Проверяет, что поля не пустые
        3. Проверяет капчу (пазл)
        4. Проверяет логин/пароль в базе данных
        5. Открывает соответствующее окно (администратора или пользователя)
        """
        # Получаем текст из полей ввода
        # .text() — метод, который возвращает текст в поле
        # .strip() — удаляет пробелы в начале и конце (например, " admin " → "admin")
        login = self.login_field.text().strip()
        password = self.password_field.text()

        # Проверяем, что поля не пустые
        # if not login — это проверка "если login пустой"
        if not login or not password:
            # QMessageBox.warning — показывает окно с предупреждением
            QMessageBox.warning(
                self,           # Родительское окно (для позиционирования)
                "Ошибка ввода", # Заголовок окна
                "Пожалуйста, заполните все поля"  # Текст сообщения
            )
            return  # Выходим из функции (не продолжаем авторизацию)

        # Проверяем капчу (пазл)
        # self.findChild — ищет дочерний элемент с указанным классом и именем
        # CaptchaWidget — это класс нашего виджета капчи
        # "captcha_widget" — это имя элемента из .ui файла
        captcha_widget = self.findChild(CaptchaWidget, "captcha_widget")
        
        # is_captcha_solved() — метод, который возвращает True, если пазл собран
        # if captcha_widget else False — если captcha_widget не найден, считаем, что капча не пройдена
        captcha_solved = captcha_widget.is_captcha_solved() if captcha_widget else False

        # Пробуем авторизовать пользователя
        try:
            # auth_module.authenticate — проверяет логин/пароль в базе данных
            # Возвращает словарь с данными пользователя: {"id": 1, "login": "admin", "role": "Администратор", ...}
            user = self.auth_module.authenticate(login, password, captcha_solved)
            
            # Показываем сообщение об успешной авторизации
            self.auth_module.show_success_message(self)

            # Определяем роль пользователя и открываем соответствующее окно
            if user["role"] == "Администратор":
                # Если роль "Администратор" — открываем панель администратора
                self._open_admin_panel(user)
            else:
                # Иначе — открываем панель пользователя
                self._open_user_panel(user)

            # Закрываем окно авторизации
            self.close()

        # Обработка ошибок (исключений)
        except UserNotFoundError:
            # Пользователь с таким логином не найден
            self.auth_module.show_auth_message(self, UserNotFoundError(login))
        except UserBlockedError:
            # Пользователь заблокирован
            self.auth_module.show_auth_message(self, UserBlockedError(login))
        except IncorrectCredentialsError:
            # Неверный логин или пароль
            self.auth_module.show_auth_message(
                self, 
                IncorrectCredentialsError(self.auth_module.MAX_PASSWORD_ATTEMPTS)
            )
        except AuthenticationError as e:
            # Какая-то другая ошибка авторизации
            QMessageBox.critical(self, "Ошибка", str(e))

    def _open_admin_panel(self, user):
        """
        Открывает панель администратора.
        
        Создаёт объект AdminPanel и показывает его.
        """
        self.admin_window = AdminPanel(user)  # Создаём окно администратора
        self.admin_window.show()  # Показываем окно

    def _open_user_panel(self, user):
        """
        Открывает панель пользователя.
        
        Создаёт объект UserPanel и показывает его.
        """
        self.user_window = UserPanel(user)  # Создаём окно пользователя
        self.user_window.show()  # Показываем окно

    def closeEvent(self, event):
        """
        Вызывается, когда окно закрывается.
        
        Здесь мы закрываем подключение к базе данных.
        Это важно — если не закрыть подключение, оно останется открытым.
        """
        db_manager.disconnect()  # Закрываем соединение с базой данных
        event.accept()  # Разрешаем закрытие окна


# ==================== ПАНЕЛЬ АДМИНИСТРАТОРА ====================
class AdminPanel(QMainWindow):
    """
    Панель администратора.
    
    Это окно доступно только пользователям с ролью "Администратор".
    Здесь можно:
    - Добавлять новых пользователей
    - Редактировать существующих
    - Снимать блокировку
    - Удалять пользователей
    """

    def __init__(self, current_user):
        """
        Конструктор класса.
        
        Args:
            current_user — словарь с данными текущего пользователя
                          (например: {"id": 1, "login": "admin", "role": "Администратор"})
        """
        super().__init__()  # Инициализируем родительский класс (QMainWindow)
        self.current_user = current_user  # Сохраняем данные текущего пользователя
        self.user_manager = UserManager(self)  # Создаём модуль управления пользователями

        # Загружаем .ui файл для панели администратора
        ui_path = os.path.join(PROJECT_ROOT, "ui", "admin_panel.ui")
        uic.loadUi(ui_path, self)

        # Устанавливаем имя пользователя в заголовке
        # f"Пользователь: {current_user['login']}" — это f-строка
        # {} — это место, куда подставляется значение
        self.lbl_current_user.setText(f"Пользователь: {current_user['login']}")

        # Подключаем все кнопки к их обработчикам
        self.btn_logout.clicked.connect(self._on_logout)
        self.btn_add_user.clicked.connect(self._on_add_user)
        self.btn_edit_user.clicked.connect(self._on_edit_user)
        self.btn_unblock_user.clicked.connect(self._on_unblock_user)
        self.btn_delete_user.clicked.connect(self._on_delete_user)
        self.tbl_users.cellClicked.connect(self._on_cell_clicked)

        # Загружаем таблицу пользователей
        self._load_users()

        # Применяем стили
        self._apply_styles()

    def _apply_styles(self):
        """Применяет CSS-стили к окну."""
        style_path = os.path.join(PROJECT_ROOT, "resources", "styles", "main.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _load_users(self):
        """Загружает таблицу пользователей из базы данных."""
        self.user_manager.load_users_table(self.tbl_users)

    def _on_logout(self):
        """Выход из системы."""
        self.close()  # Закрываем текущее окно
        self.login_win = LoginWindow()  # Создаём новое окно авторизации
        self.login_win.show()  # Показываем его

    def _on_add_user(self):
        """
        Добавление нового пользователя.
        
        Эта функция вызывается, когда администратор нажимает кнопку "Добавить".
        """
        # Получаем данные из полей ввода
        login = self.txt_add_login.text().strip()
        password = self.txt_add_password.text()
        role = self.cmb_add_role.currentText()  # Получаем выбранную роль из выпадающего списка

        # Проверяем, что поля не пустые
        if not login or not password:
            QMessageBox.warning(self, "Ошибка ввода", "Заполните логин и пароль")
            return

        # Вызываем метод add_user из модуля UserManager
        # Он проверяет уникальность логина и добавляет пользователя в базу
        self.user_manager.add_user(login, password, role)
        
        # Обновляем таблицу пользователей (чтобы показать нового пользователя)
        self._load_users()

        # Очищаем поля ввода
        self.txt_add_login.clear()
        self.txt_add_password.clear()

    def _on_cell_clicked(self, row, column):
        """
        Обработка клика по ячейке таблицы.
        
        Args:
            row — номер строки (0, 1, 2, ...)
            column — номер столбца (0, 1, 2, ...)
        
        Здесь можно добавить логику выделения строки.
        """
        pass  # Пока ничего не делаем

    def _on_edit_user(self):
        """
        Редактирование пользователя.
        
        Открывает диалоговое окно для изменения данных пользователя.
        """
        # Получаем выделенные строки в таблице
        selected_rows = self.tbl_users.selectedItems()
        
        # Если ничего не выделено — показываем предупреждение
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для редактирования")
            return

        # Получаем данные из выделенной строки
        # selected_rows[0] — это первая выделенная ячейка
        # .row() — возвращает номер строки
        row = selected_rows[0].row()
        
        # Получаем данные из ячеек
        # .item(row, column) — возвращает ячейку в указанной строке и столбце
        # .text() — возвращает текст в ячейке
        user_id = int(self.tbl_users.item(row, 0).text())  # ID пользователя
        old_login = self.tbl_users.item(row, 1).text()  # Старый логин
        old_role = self.tbl_users.item(row, 2).text()  # Старая роль

        # Открываем диалоговое окно для редактирования
        dialog = EditUserDialog(self, old_login, old_role)
        
        # dialog.exec() — показывает диалоговое окно и ждёт, пока пользователь закроет его
        # QDialog.DialogCode.Accepted — это константа, если пользователь нажал "OK"
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Получаем новые данные из диалога
            new_login, new_password, new_role = dialog.get_data()
            
            # Если логин и пароль не пустые — обновляем пользователя
            if new_login and new_password:
                self.user_manager.edit_user(user_id, new_login, new_password, new_role)
                self._load_users()  # Обновляем таблицу

    def _on_unblock_user(self):
        """
        Снятие блокировки с пользователя.
        
        Если пользователь был заблокирован (например, за 3 неверных попытки пароля),
        администратор может снять блокировку.
        """
        selected_rows = self.tbl_users.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return

        row = selected_rows[0].row()
        user_id = int(self.tbl_users.item(row, 0).text())
        login = self.tbl_users.item(row, 1).text()

        # Вызываем метод unblock_user из модуля UserManager
        self.user_manager.unblock_user(user_id, login)
        self._load_users()  # Обновляем таблицу

    def _on_delete_user(self):
        """
        Удаление пользователя.
        
        Сначала показываем диалог подтверждения, чтобы случайно не удалить пользователя.
        """
        selected_rows = self.tbl_users.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return

        row = selected_rows[0].row()
        user_id = int(self.tbl_users.item(row, 0).text())
        login = self.tbl_users.item(row, 1).text()

        # Показываем диалог подтверждения
        # QMessageBox.question — это окно с вопросом (Да/Нет)
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить пользователя '{login}'?\n\n"
            "Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # По умолчанию выбираем "Нет"
        )

        # Если пользователь нажал "Да" — удаляем
        if reply == QMessageBox.StandardButton.Yes:
            self.user_manager.delete_user(user_id, login)
            self._load_users()  # Обновляем таблицу

    def closeEvent(self, event):
        """Вызывается, когда окно закрывается."""
        db_manager.disconnect()  # Закрываем соединение с базой данных
        event.accept()  # Разрешаем закрытие окна


# ==================== ДИАЛОГ РЕДАКТИРОВАНИЯ ====================
class EditUserDialog(QDialog):
    """
    Диалоговое окно для редактирования пользователя.
    
    Это всплывающее окно, которое появляется при нажатии кнопки "Редактировать".
    Здесь можно изменить логин, пароль и роль пользователя.
    """

    def __init__(self, parent, old_login, old_role):
        """
        Конструктор класса.
        
        Args:
            parent — родительское окно (AdminPanel)
            old_login — текущий логин пользователя
            old_role — текущая роль пользователя
        """
        super().__init__(parent)  # Инициализируем родительский класс (QDialog)
        self.setWindowTitle("Редактировать пользователя")  # Заголовок окна
        self.setModal(True)  # Модальное окно — нельзя работать с основным окном, пока это окно открыто

        # Создаём вертикальный layout (элементы располагаются сверху вниз)
        layout = QVBoxLayout(self)

        # Создаём поле для логина
        self.txt_login = QLineEdit()
        self.txt_login.setText(old_login)  # Устанавливаем текущий логин
        layout.addWidget(QLabel("Логин:"))  # Добавляем метку "Логин:"
        layout.addWidget(self.txt_login)  # Добавляем поле ввода

        # Создаём поле для пароля
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)  # Скрываем символы (показываем звёздочки)
        self.txt_password.setPlaceholderText("Оставьте пустым, если не меняете")  # Подсказка в поле
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.txt_password)

        # Создаём выпадающий список для роли
        self.cmb_role = QComboBox()
        self.cmb_role.addItem("Пользователь")  # Добавляем вариант "Пользователь"
        self.cmb_role.addItem("Администратор")  # Добавляем вариант "Администратор"
        
        # Если текущая роль "Администратор" — выбираем её по умолчанию
        if old_role == "Администратор":
            self.cmb_role.setCurrentIndex(1)  # 1 — это второй элемент (нумерация с 0)
        
        layout.addWidget(QLabel("Роль:"))
        layout.addWidget(self.cmb_role)

        # Создаём кнопки "OK" и "Cancel"
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        # Когда пользователь нажимает "OK" — вызываем self.accept()
        # Когда пользователь нажимает "Cancel" — вызываем self.reject()
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        """
        Возвращает данные из диалога.
        
        Returns:
            Кортеж (tuple) с тремя значениями: (login, password, role)
        """
        return (
            self.txt_login.text().strip(),  # Логин (без пробелов)
            self.txt_password.text(),        # Пароль
            self.cmb_role.currentText()      # Выбранная роль
        )


# ==================== ПАНЕЛЬ ПОЛЬЗОВАТЕЛЯ ====================
class UserPanel(QMainWindow):
    """
    Панель пользователя.
    
    Это окно доступно всем пользователям (не только администраторам).
    Здесь можно:
    - Просматривать заказы
    - Просматривать продукцию
    - Видеть информацию о своём профиле
    """

    def __init__(self, current_user):
        """
        Конструктор класса.
        
        Args:
            current_user — словарь с данными текущего пользователя
        """
        super().__init__()  # Инициализируем родительский класс (QMainWindow)
        self.current_user = current_user  # Сохраняем данные текущего пользователя

        # Загружаем .ui файл для панели пользователя
        ui_path = os.path.join(PROJECT_ROOT, "ui", "user_panel.ui")
        uic.loadUi(ui_path, self)

        # Устанавливаем имя пользователя в заголовке
        self.lbl_current_user.setText(f"Пользователь: {current_user['login']}")

        # Заполняем информацию о профиле
        self.lbl_profile_login_value.setText(current_user["login"])
        self.lbl_profile_role_value.setText(current_user["role"])

        # Подключаем кнопку "Выйти"
        self.btn_logout.clicked.connect(self._on_logout)

        # Загружаем данные (заказы и продукцию)
        self._load_orders()
        self._load_products()

        # Применяем стили
        self._apply_styles()

    def _apply_styles(self):
        """Применяет CSS-стили к окну."""
        style_path = os.path.join(PROJECT_ROOT, "resources", "styles", "main.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _load_orders(self):
        """
        Загружает заказы из базы данных и отображает их в таблице.
        
        Эта функция:
        1. Получает список заказов из базы данных
        2. Создаёт строки в таблице
        3. Заполняет ячейки данными (номер заказа, дата, исполнитель)
        """
        try:
            # Получаем заказы из базы данных
            orders = db_manager.get_orders()
            
            # Получаем таблицу заказов из интерфейса
            tbl = self.tbl_orders
            
            # Устанавливаем количество строк в таблице
            tbl.setRowCount(len(orders))

            # Заполняем каждую строку данными
            # enumerate(orders) — это цикл, который даёт номер строки и заказ
            for row, order in enumerate(orders):
                # row + 1 — нумерация строк начинается с 1 (а не с 0)
                tbl.setItem(row, 0, QTableWidgetItem(str(row + 1)))  # Номер
                tbl.setItem(row, 1, QTableWidgetItem(str(order["order_number"])))  # Номер заказа
                tbl.setItem(row, 2, QTableWidgetItem(str(order["order_date"])[:10]))  # Дата (первые 10 символов)
                tbl.setItem(row, 3, QTableWidgetItem(order["executor"]))  # Исполнитель
        except Exception as e:
            # Если произошла ошибка — показываем предупреждение
            QMessageBox.warning(self, "Предупреждение", f"Не удалось загрузить заказы:\n{e}")

    def _load_products(self):
        """
        Загружает продукцию из базы данных и отображает её в таблице.
        """
        try:
            # Получаем продукцию из базы данных
            products = db_manager.get_products()
            
            # Получаем таблицу продукции
            tbl = self.tbl_products
            
            # Устанавливаем количество строк
            tbl.setRowCount(len(products))

            # Заполняем каждую строку данными
            for row, product in enumerate(products):
                tbl.setItem(row, 0, QTableWidgetItem(product["code"]))  # Код продукции
                tbl.setItem(row, 1, QTableWidgetItem(product["name"]))  # Наименование
        except Exception as e:
            # Если произошла ошибка — показываем предупреждение
            QMessageBox.warning(self, "Предупреждение", f"Не удалось загрузить продукцию:\n{e}")

    def _on_logout(self):
        """Выход из системы."""
        self.close()  # Закрываем текущее окно
        self.login_win = LoginWindow()  # Создаём новое окно авторизации
        self.login_win.show()  # Показываем его

    def closeEvent(self, event):
        """Вызывается, когда окно закрывается."""
        db_manager.disconnect()  # Закрываем соединение с базой данных
        event.accept()  # Разрешаем закрытие окна


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================
def main():
    """
    Точка входа приложения.
    
    Эта функция запускается, когда мы запускаем файл main.py.
    Она:
    1. Создаёт объект QApplication (это "движок" приложения)
    2. Настраивает шрифт
    3. Подключается к базе данных
    4. Открывает окно авторизации
    5. Запускает главный цикл событий (приложение начинает работать)
    """
    # Создаём объект QApplication
    # sys.argv — это аргументы командной строки (обычно пустой список)
    app = QApplication(sys.argv)

    # Настраиваем шрифт по умолчанию для всего приложения
    font = QFont("Segoe UI", 10)  # Шрифт "Segoe UI", размер 10
    app.setFont(font)

    # Подключаемся к базе данных
    # db_manager.connect() — устанавливает соединение с PostgreSQL
    # Мы не выходим при ошибке, потому что база данных может быть недоступна на старте
    db_manager.connect()

    # Создаём и показываем окно авторизации
    login_window = LoginWindow()  # Создаём объект LoginWindow
    login_window.show()  # Показываем окно

    # Запускаем главный цикл со��ытий
    # app.exec() — это бесконечный цикл, который обрабатывает события (клики, нажатия клавиш)
    # Приложение работает, пока пользователь не закроет его
    # sys.exit() — завершает программу и возвращает код выхода
    sys.exit(app.exec())


# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================
# Эта проверка выполняется, только если мы запускаем файл main.py напрямую
# Если мы импортируем main.py в другой файл — этот код НЕ выполнится
if __name__ == "__main__":
    import traceback as tb  # Модуль для вывода подробной информации об ошибках
    try:
        main()  # Запускаем функцию main()
    except Exception as e:
        # Если произошла ошибка — показываем её в консоли
        print(f"\n!!! ОШИБКА: {e}")  # Текст ошибки
        print(tb.format_exc())  # Подробная информация (stack trace)
        sys.exit(1)  # Завершаем программу с кодом ошибки 1
