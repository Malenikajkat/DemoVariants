"""
Модуль интерактивной капчи (пазл).
Стоматология «Улыбка» — Задание 4

Этот модуль создаёт виджет капчи — интерактивную проверку,
которая требует от пользователя собрать пазл.

Как работает капча:
1. Загружаются изображения из папки images/ (1.png, 2.png, 3.png, 4.png)
2. Изображения отображаются как кусочки пазла
3. Пользователь кликает на кусочки, чтобы отметить их как собранные
4. Когда все кусочки отмечены — капча считается пройденной

Зачем нужна капча?
------------------
Капча защищает систему от автоматических атак (ботов).
Бот не сможет собрать пазл, а живой пользователь — сможет.

Классы:
- PuzzlePiece — кусочек пазла (отображает изображение и номер)
- CaptchaWidget — виджет капчи (содержит все кусочки и управляет ими)

Пример использования:
    # В Qt Designer создаём виджет с именем "captcha_widget"
    # В коде приложения:
    captcha = self.findChild(CaptchaWidget, "captcha_widget")
    if captcha.is_captcha_solved():
        print("Капча пройдена!")
"""

# Импортируем random для перемешивания
import random
# Импортируем Path для работы с путями к файлам
from pathlib import Path
# Импортируем классы для создания интерфейса
from PyQt6.QtWidgets import (
    QWidget,          # Базовый класс для виджетов
    QLabel,           # Текстовая метка
    QVBoxLayout,      # Вертикальный layout (элементы сверху вниз)
    QHBoxLayout,      # Горизонтальный layout (элементы слева направо)
    QPushButton,      # Кнопка
    QMessageBox,      # Окно с сообщением
    QSizePolicy       # Размер и политика растяжения виджета
)
# Импортируем классы для работы с графикой
from PyQt6.QtCore import Qt, pyqtSignal  # Qt — константы, pyqtSignal — сигналы
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor  # Pixmap — изображение, Painter — рисование


# Путь к папке с кусочками пазла (корень проекта /images)
# __file__ — это путь к текущему файлу (captcha_module.py)
# .parent — это родительская папка (src/)
# .parent.parent — это папка проекта (proba/)
IMAGES_DIR = Path(__file__).parent.parent / "images"


class PuzzlePiece(QLabel):
    """
    Кусочек пазла.
    
    Это виджет, который отображает один кусочек изображения.
    При клике на кусочек он отмечается как "собранный" (зелёная рамка).
    
    Атрибуты:
        piece_number — номер кусочка (1, 2, 3, ...)
        is_selected — True, если кусочек отмечен как собранный
    
    Пример использования:
        piece = PuzzlePiece(pixmap, 1, parent)
        piece.clicked.connect(lambda: print("Кусочек собран!"))
    """

    # Создаём сигнал, который будет отправляться при клике
    # pyqtSignal() — это способ создать сигнал в PyQt
    # Сигнал — это способ сказать "когда-нибудь в будущем вызови эту функцию"
    clicked = pyqtSignal()

    def __init__(self, pixmap, number, parent=None):
        """
        Конструктор класса.
        
        Args:
            pixmap — изображение кусочка (объект QPixmap)
            number — номер кусочка (1, 2, 3, ...)
            parent — родительский виджет (обычно это CaptchaWidget)
        """
        super().__init__(parent)  # Инициализируем родительский класс (QLabel)
        self.piece_number = number  # Сохраняем номер кусочка
        self.is_selected = False    # Изначально кусочек не отмечен
        
        # Устанавливаем изображение кусочка
        self.setPixmap(pixmap)
        self.setScaledContents(False)  # Не масштабируем автоматически
        
        # Устанавливаем фиксированный размер (размер изображения)
        self.setFixedSize(pixmap.size())
        
        # Применяем стиль (рамка, фон)
        self.setStyleSheet(
            "border: 2px solid #1565C0; background-color: #E3F2FD; border-radius: 4px;"
        )
        # Меняем курсор на "руку" при наведении
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """
        Обработка клика по кусочку.
        
        Эта функция вызывается, когда пользователь кликает на кусочек.
        Она отправляет сигнал clicked, который обрабатывается в CaptchaWidget.
        
        Args:
            event — объект события мыши
        """
        # Проверяем, что это левая кнопка мыши
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()  # Отправляем сигнал "клик"
        super().mousePressEvent(event)  # Вызываем метод родительского класса

    def paintEvent(self, event):
        """
        Рисует номер кусочка поверх изображения.
        
        Эта функция вызывается каждый раз, когда виджет нужно перерисовать.
        Мы используем её, чтобы нарисовать номер кусочка.
        
        Args:
            event — событие перерисовки
        """
        super().paintEvent(event)  # Сначала рисуем изображение
        
        # Создаём объект для рисования
        painter = QPainter(self)
        
        # Настраиваем цвет и размер шрифта
        painter.setPen(QPen(QColor("#FFFFFF"), 3))
        painter.setFont(self.font())
        
        # Рисуем номер кусочка
        painter.drawText(
            self.rect(),  # Область рисования
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,  # Выравнивание
            f"#{self.piece_number}"  # Текст номера
        )
        
        # Заканчиваем рисование
        painter.end()

    def mark_as_selected(self):
        """Отмечает кусочек как собранный (зелёная рамка)."""
        self.is_selected = True
        self.setStyleSheet(
            "border: 3px solid #2E7D32; background-color: #C8E6C9; font-weight: bold;"
        )

    def mark_as_unselected(self):
        """Снимает отметку с кусочка (синяя рамка)."""
        self.is_selected = False
        self.setStyleSheet(
            "border: 2px solid #1565C0; background-color: #E3F2FD;"
        )


class CaptchaWidget(QWidget):
    """
    Виджет интерактивной капчи-пазла.
    
    Этот виджет загружает кусочки пазла из папки images/ и отображает их.
    Пользователь кликает на кусочки, чтобы отметить их как собранные.
    
    Атрибуты:
        pieces — список всех кусочков пазла (PuzzlePiece)
        selected_pieces — множество отмеченных кусочков
        is_solved — True, если все кусочки отмечены
    
    Пример использования:
        # В Qt Designer создаём виджет с именем "captcha_widget"
        # В коде:
        captcha = self.findChild(CaptchaWidget, "captcha_widget")
        if captcha.is_captcha_solved():
            print("Капча пройдена!")
    """

    def __init__(self, parent=None):
        """
        Конструктор класса.
        
        Args:
            parent — родительский виджет (обычно это LoginWindow)
        """
        super().__init__(parent)  # Инициализируем родительский класс (QWidget)
        
        # Инициализируем переменные
        self.pieces = []           # Список всех кусочков
        self.selected_pieces = set()  # Множество отмеченных кусочков
        self.is_solved = False     # Флаг, что пазл собран
        self.piece_count = 0       # Количество кусочков
        
        # Загружаем кусочки пазла
        self.piece_pixmaps = self._load_pieces()
        self.piece_count = len(self.piece_pixmaps)
        
        # Создаём интерфейс
        self._setup_ui()

    def _load_pieces(self):
        """
        Загружает кусочки пазла из папки images.
        
        Эта функция ищет файлы 1.png, 2.png, 3.png, 4.png в папке images/
        и загружает их как изображения.
        
        Returns:
            Список объектов QPixmap (изображений)
        """
        pixmaps = []  # Список для хранения изображений
        
        # Ищем файлы 1.png, 2.png, 3.png, 4.png
        for i in range(1, 100):  # Проверяем до 99 файлов
            file_path = IMAGES_DIR / f"{i}.png"  # Формируем путь к файлу
            if file_path.exists():  # Проверяем, существует ли файл
                pixmap = QPixmap(str(file_path))  # Загружаем изображение
                if not pixmap.isNull():  # Проверяем, что изображение загружено
                    pixmaps.append(pixmap)  # Добавляем в список
            else:
                # Если файл не найден, проверяем другие расширения
                for ext in [".jpg", ".jpeg", ".bmp", ".gif"]:
                    alt_path = IMAGES_DIR / f"{i}{ext}"
                    if alt_path.exists():
                        pixmap = QPixmap(str(alt_path))
                        if not pixmap.isNull():
                            pixmaps.append(pixmap)
                        break
                else:
                    # Если файл не найден ни в одном формате — останавливаемся
                    break
        
        # Если не нашли нумерованные файлы — ищем все PNG в папке
        if not pixmaps:
            for file_path in sorted(IMAGES_DIR.glob("*.png")):
                pixmap = QPixmap(str(file_path))
                if not pixmap.isNull():
                    pixmaps.append(pixmap)
        
        # Если всё ещё нет — генерируем заглушки
        if not pixmaps:
            pixmaps = self._generate_placeholder_pieces()
        
        return pixmaps

    def _generate_placeholder_pieces(self):
        """
        Генерирует заглушки, если нет файлов изображений.
        
        Эта функция создаёт цветные квадраты с номерами,
        если в папке images/ нет файлов.
        
        Returns:
            Список объектов QPixmap (заглушек)
        """
        pixmaps = []
        # Цвета для заглушек
        colors = [Qt.GlobalColor.lightBlue, Qt.GlobalColor.lightGreen, 
                  Qt.GlobalColor.lightYellow, Qt.GlobalColor.lightGray]
        
        # Создаём 4 заглушки
        for i in range(4):
            pixmap = QPixmap(80, 80)  # Создаём изображение 80x80
            pixmap.fill(colors[i % len(colors)])  # Закрашиваем цветом
            
            # Рисуем номер
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor("#000000"), 2))
            painter.setFont(painter.font())
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, f"#{i+1}")
            painter.end()
            
            pixmaps.append(pixmap)
        
        return pixmaps

    def _setup_ui(self):
        """
        Создаёт интерфейс виджета.
        
        Эта функция создаёт все элементы интерфейса:
        - Заголовок
        - Область предпросмотра
        - Кусочки пазла
        - Кнопку перезапуска
        - Статус сборки
        """
        # Создаём вертикальный layout (элементы сверху вниз)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Отступы
        layout.setSpacing(5)  # Расстояние между элементами
        
        # Заголовок
        lbl_header = QLabel("Соберите пазл — кликайте на кусочки:")
        lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_header.setStyleSheet("font-weight: bold; color: #1565C0; font-size: 14px;")
        layout.addWidget(lbl_header)
        
        # Область предпросмотра (показываем, что нужно собрать)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setText("🧩 Соберите все кусочки")
        self.preview_label.setStyleSheet("""
            background-color: #F5F5F5; 
            border: 2px dashed #BDBDBD; 
            border-radius: 4px;
            font-size: 24px;
            padding: 20px;
        """)
        layout.addWidget(self.preview_label)
        
        # Контейнер для кусочков пазла
        self.pieces_container = QWidget()
        self.pieces_container.setMinimumSize(200, 100)  # Минимальный размер
        self.pieces_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        pieces_layout = QHBoxLayout(self.pieces_container)  # Горизонтальный layout
        pieces_layout.setContentsMargins(10, 10, 10, 10)
        pieces_layout.setSpacing(10)
        
        # Создаём кусочки с масштабированием
        target_size = 80  # Размер каждого кусочка
        for i, pixmap in enumerate(self.piece_pixmaps):
            # Масштабируем пикмап до target_size x target_size
            scaled_pixmap = pixmap.scaled(
                target_size, target_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            # Создаём кусочек пазла
            piece = PuzzlePiece(scaled_pixmap, i + 1, self.pieces_container)
            # Подключаем сигнал clicked к функции _on_piece_clicked
            piece.clicked.connect(lambda p=piece: self._on_piece_clicked(p))
            self.pieces.append(piece)  # Добавляем в список
            pieces_layout.addWidget(piece)  # Добавляем в layout
        
        layout.addWidget(self.pieces_container)  # Добавляем контейнер в layout
        
        # Кнопка перезапуска
        self.btn_restart = QPushButton("🔄 Перезапустить пазл")
        self.btn_restart.clicked.connect(self._restart_puzzle)
        self.btn_restart.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #1565C0;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(self.btn_restart)
        
        # Статус сборки
        self.status_label = QLabel(f"Собрано: 0 / {self.piece_count}")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #757575; font-size: 12px;")
        layout.addWidget(self.status_label)

    def _on_piece_clicked(self, piece):
        """
        Обработка клика по кусочку.
        
        Эта функция вызывается, когда пользователь кликает на кусочек.
        Она отмечает или снимает отметку с кусочка.
        
        Args:
            piece — объект PuzzlePiece, на который кликнули
        """
        # Если пазл уже собран — ничего не делаем
        if self.is_solved:
            return
        
        # Проверяем, отмечен ли кусочек
        if piece not in self.selected_pieces:
            # Отмечаем как собранный
            self.selected_pieces.add(piece)
            piece.mark_as_selected()
        else:
            # Снимаем отметку
            self.selected_pieces.discard(piece)
            piece.mark_as_unselected()
        
        # Обновляем статус
        self.status_label.setText(f"Собрано: {len(self.selected_pieces)} / {self.piece_count}")
        
        # Проверяем, все ли кусочки отмечены
        if len(self.selected_pieces) == self.piece_count:
            self.is_solved = True
            self.status_label.setText("✓ Пазл собран!")
            self.status_label.setStyleSheet("color: #2E7D32; font-weight: bold; font-size: 12px;")
            
            # Показываем сообщение об успехе
            QMessageBox.information(
                self,
                "✓ Капча пройдена",
                "Вы успешно собрали пазл. Можете авторизоваться."
            )
            self.setStyleSheet("background-color: #C8E6C9; border-radius: 8px;")

    def _restart_puzzle(self):
        """Перезапускает пазл (снимает все отметки)."""
        self.selected_pieces.clear()  # Очищаем множество отмеченных
        self.is_solved = False        # Сбрасываем флаг
        
        # Снимаем отметки со всех кусочков
        for piece in self.pieces:
            piece.mark_as_unselected()
        
        # Обновляем статус
        self.status_label.setText(f"Собрано: 0 / {self.piece_count}")
        self.status_label.setStyleSheet("color: #757575; font-size: 12px;")
        self.setStyleSheet("")  # Сбрасываем стиль

    def is_captcha_solved(self):
        """
        Возвращает True, если капча пройдена.
        
        Эта функция вызывается из LoginWindow при нажатии кнопки "Войти".
        
        Returns:
            True — если все кусочки отмечены
            False — если не все
        """
        return self.is_solved
