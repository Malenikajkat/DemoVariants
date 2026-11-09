# ВАРИАНТ 15: Разработка модуля уведомлений и оповещений

---

## Задание

Разработать систему уведомлений информационной системы с поддержкой различных каналов доставки (внутриприложение, email, log-файл) и приоритизацией сообщений.

### Цель

Оценка умения выполнять интеграцию модулей в программное обеспечение, организовывать заданную интеграцию на базе имеющейся архитектуры.

### Исходные данные

База данных PostgreSQL содержит таблицы из инвариантной части. Требуется добавить таблицу уведомлений.

### Требования к выполнению

#### Часть 1. Модуль уведомлений

1. Создать модуль `notification_system.py`:

```python
import psycopg2
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class NotificationChannel(Enum):
    """Каналы доставки уведомлений"""
    IN_APP = "in_app"
    EMAIL = "email"
    LOG_FILE = "log_file"

class NotificationPriority(Enum):
    """Уровни приоритета"""
    LOW = "Низкий"
    MEDIUM = "Средний"
    HIGH = "Высокий"
    CRITICAL = "Критический"

@dataclass
class Notification:
    """Уведомление"""
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channel: NotificationChannel = NotificationChannel.IN_APP
    recipient_id: Optional[int] = None
    metadata: Dict = field(default_factory=dict)

class NotificationSystem:
    """Система уведомлений"""
    
    def __init__(self, db_params: dict, log_file: str = "notifications.log"):
        self.db_params = db_params
        self.logger = logging.getLogger("notifications")
        self.logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def send_notification(self, notification: Notification) -> int:
        """Отправка уведомления через указанный канал"""
        notification_id = self._save_to_db(notification)
        
        # Доставка через все указанные каналы
        if notification.channel == NotificationChannel.IN_APP:
            self._deliver_in_app(notification)
        
        if notification.channel == NotificationChannel.EMAIL:
            self._deliver_email(notification)
        
        if notification.channel == NotificationChannel.LOG_FILE:
            self._deliver_log(notification)
        
        # Обновление статуса
        self._update_status(notification_id, "sent")
        
        return notification_id
    
    def send_order_status_change(self, user_id: int, order_id: int,
                                   old_status: str, new_status: str):
        """Уведомление об изменении статуса заказа"""
        notification = Notification(
            title=f"Статус заказа #{order_id} изменён",
            message=f"Статус изменён с '{old_status}' на '{new_status}'",
            priority=NotificationPriority.HIGH,
            channel=NotificationChannel.IN_APP,
            recipient_id=user_id,
            metadata={"order_id": order_id, "old_status": old_status, 
                     "new_status": new_status}
        )
        return self.send_notification(notification)
    
    def send_low_stock_alert(self, product_name: str, current_stock: int,
                               threshold: int = 10):
        """Уведомление о низком остатке"""
        notification = Notification(
            title="Низкий остаток товара",
            message=f"Товар '{product_name}': осталось {current_stock} шт. "
                    f"(порог: {threshold})",
            priority=NotificationPriority.CRITICAL,
            channel=NotificationChannel.IN_APP,
            metadata={"product_name": product_name, 
                     "current_stock": current_stock,
                     "threshold": threshold}
        )
        return self.send_notification(notification)
    
    def send_daily_summary(self, user_id: int, order_count: int,
                            total_revenue: float):
        """Ежедневная сводка"""
        notification = Notification(
            title="Ежедневная сводка",
            message=f"За сегодня: {order_count} заказов на сумму "
                    f"{total_revenue:,.2f} ₽",
            priority=NotificationPriority.LOW,
            channel=NotificationChannel.IN_APP,
            recipient_id=user_id
        )
        return self.send_notification(notification)
    
    def get_user_notifications(self, user_id: int, 
                                unread_only: bool = False) -> List[Dict]:
        """Получение уведомлений пользователя"""
        query = """
        SELECT id, title, message, priority, channel, is_read, created_at
        FROM notifications
        WHERE recipient_id = %s
        """
        params = [user_id]
        
        if unread_only:
            query += " AND is_read = FALSE"
        
        query += " ORDER BY created_at DESC"
        
        return self._execute_query(query, tuple(params))
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Отметка уведомления как прочитанного"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE notifications 
                           SET is_read = TRUE, read_at = NOW()
                           WHERE id = %s AND recipient_id = %s""",
                        (notification_id, user_id)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception:
            return False
    
    def get_unread_count(self, user_id: int) -> int:
        """Количество непрочитанных уведомлений"""
        query = """
        SELECT COUNT(*) FROM notifications
        WHERE recipient_id = %s AND is_read = FALSE
        """
        result = self._execute_query(query, (user_id,))
        return result[0]["count"] if result else 0
    
    def _save_to_db(self, notification: Notification) -> int:
        """Сохранение уведомления в БД"""
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO notifications 
                       (title, message, priority, channel, recipient_id, 
                        metadata, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, NOW())
                       RETURNING id""",
                    (
                        notification.title,
                        notification.message,
                        notification.priority.value,
                        notification.channel.value,
                        notification.recipient_id,
                        notification.metadata
                    )
                )
                return cur.fetchone()[0]
    
    def _deliver_in_app(self, notification: Notification):
        """Доставка внутри приложения (логирование)"""
        self.logger.info(
            f"[{notification.priority.value}] {notification.title}: "
            f"{notification.message}"
        )
    
    def _deliver_email(self, notification: Notification):
        """Доставка по email (заглушка)"""
        self.logger.info(f"[EMAIL] {notification.title}")
    
    def _deliver_log(self, notification: Notification):
        """Доставка в log-файл"""
        self.logger.warning(f"[LOG] {notification.title}: {notification.message}")
    
    def _update_status(self, notification_id: int, status: str):
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE notifications SET status = %s WHERE id = %s",
                        (status, notification_id)
                    )
                    conn.commit()
        except Exception:
            pass
    
    def _execute_query(self, query: str, params=None) -> List[Dict]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
```

#### Часть 2. SQL-схема

2. Создать `migrations/005_notifications.sql`:

```sql
-- Таблица уведомлений
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'Средний',
    channel VARCHAR(20) NOT NULL DEFAULT 'in_app',
    recipient_id INTEGER REFERENCES users(id),
    metadata JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_notifications_recipient ON notifications(recipient_id);
CREATE INDEX idx_notifications_read ON notifications(is_read);
CREATE INDEX idx_notifications_created ON notifications(created_at);

-- Триггер: автоматическая отметка при чтении
CREATE OR REPLACE FUNCTION mark_notification_read()
RETURNS TRIGGER AS $$
BEGIN
    NEW.is_read := TRUE;
    NEW.read_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### Часть 3. GUI-панель уведомлений

3. Создать форму `notification_panel.ui` и приложение `notification_app.py`:

Требования к интерфейсу:
- Список уведомлений с фильтрацией (все / непрочитанные)
- Цветовая индикация по приоритету (красный — критический, жёлтый — высокий)
- Кнопка «Отметить прочитанным»
- Счётчик непрочитанных уведомлений
- Форма «Отправить уведомление» (заголовок, сообщение, приоритет, канал)
- Кнопки быстрых уведомлений: «Низкий остаток», «Изменение статуса», «Сводка»

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Сохранение уведомлений в БД | 4,00 |
| Множественные каналы доставки (in_app, email, log) | 4,00 |
| Приоритизация уведомлений | 3,00 |
| Уведомления об изменении статуса заказа | 3,00 |
| Уведомления о низком остатке | 3,00 |
| Получение и фильтрация уведомлений | 4,00 |
| GUI-панель с цветовой индикацией | 3,00 |
| Обработка исключений, комментарии | 1,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- SQL-миграция уведомлений
- Таблица `users` из инвариантной части

### Инструкция для администратора ЦПДЭ

1. Применить SQL-миграцию уведомлений.
2. Убедиться, что таблица `users` существует.

### Инструкция для технического эксперта

1. Подготовить SQL-миграцию.
2. Проверить наличие psycopg2.
