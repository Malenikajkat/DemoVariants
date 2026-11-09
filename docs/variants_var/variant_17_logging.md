# ВАРИАНТ 17: Настройка логирования и аудита действий

---

## Задание

Разработать систему логирования и аудита действий пользователей информационной системы с возможностью фильтрации и экспорта журналов.

### Цель

Оценка умения выявлять технические проблемы, возникающие в процессе эксплуатации баз данных и серверов.

### Исходные данные

Информационная система включает модули авторизации, управления заказами и пользователями.

### Требования к выполнению

#### Часть 1. Система логирования

1. Создать модуль `audit_logger.py`:

```python
import logging
import json
import os
from typing import Optional, List, Dict
from datetime import datetime
from functools import wraps
import psycopg2

class AuditLogger:
    """Система логирования и аудита действий"""
    
    def __init__(self, db_params: dict, log_dir: str = "logs"):
        self.db_params = db_params
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self._setup_file_logger()
        self._setup_db_logger()
    
    def _setup_file_logger(self):
        """Настройка логирования в файлы"""
        self.file_logger = logging.getLogger("audit")
        self.file_logger.setLevel(logging.DEBUG)
        
        # Форматер
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(user)s | %(action)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Файл общих логов
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, "audit.log"),
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        self.file_logger.addHandler(file_handler)
        
        # Файл ошибок
        error_handler = logging.FileHandler(
            os.path.join(self.log_dir, "audit_errors.log"),
            encoding="utf-8"
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        self.file_logger.addHandler(error_handler)
    
    def _setup_db_logger(self):
        """Инициализация таблицы аудита в БД"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS audit_log (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id),
                            username VARCHAR(50),
                            action VARCHAR(100) NOT NULL,
                            category VARCHAR(50),
                            details TEXT,
                            ip_address VARCHAR(45),
                            user_agent TEXT,
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    conn.commit()
        except Exception:
            pass  # Таблица может быть создана ранее
    
    def log_action(self, user_id: Optional[int], username: str,
                   action: str, category: str = "general",
                   details: Optional[str] = None,
                   ip_address: Optional[str] = None,
                   level: str = "INFO"):
        """Запись действия в логи и БД"""
        extra = {
            "user": username or "anonymous",
            "action": action
        }
        
        # Логирование в файл
        log_method = getattr(self.file_logger, level.lower(), 
                            self.file_logger.info)
        log_method(details or "", extra=extra)
        
        # Логирование в БД
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO audit_log 
                           (user_id, username, action, category, details, 
                            ip_address, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
                        (user_id, username, action, category, details, ip_address)
                    )
                    conn.commit()
        except Exception:
            pass  # Файловый лог работает даже при недоступности БД
    
    def log_login(self, user_id: int, username: str, success: bool,
                  ip_address: str = None):
        """Логирование входа в систему"""
        action = "login_success" if success else "login_failed"
        details = f"IP: {ip_address}" if ip_address else ""
        self.log_action(
            user_id=user_id,
            username=username,
            action=action,
            category="authentication",
            details=details,
            ip_address=ip_address,
            level="WARNING" if not success else "INFO"
        )
    
    def log_order_created(self, user_id: int, username: str,
                           order_id: int, total: float):
        self.log_action(
            user_id=user_id,
            username=username,
            action="order_created",
            category="orders",
            details=f"Заказ #{order_id} на сумму {total:,.2f} ₽"
        )
    
    def log_user_modified(self, user_id: int, username: str,
                           target_user_id: int, changes: Dict):
        changes_json = json.dumps(changes, ensure_ascii=False)
        self.log_action(
            user_id=user_id,
            username=username,
            action="user_modified",
            category="users",
            details=f"Изменения пользователя #{target_user_id}: {changes_json}"
        )
    
    def log_data_export(self, user_id: int, username: str,
                         format: str, record_count: int):
        self.log_action(
            user_id=user_id,
            username=username,
            action="data_exported",
            category="data",
            details=f"Экспорт в {format}: {record_count} записей"
        )
    
    def get_audit_log(self, user_id: Optional[int] = None,
                       category: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       limit: int = 100) -> List[Dict]:
        """Получение журнала аудита с фильтрацией"""
        query = """
        SELECT id, user_id, username, action, category, details,
               ip_address, created_at
        FROM audit_log
        WHERE 1=1
        """
        params = []
        
        if user_id is not None:
            query += " AND user_id = %s"
            params.append(user_id)
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= %s"
            params.append(end_date)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        return self._execute_query(query, tuple(params))
    
    def get_audit_statistics(self, days: int = 7) -> Dict:
        """Статистика аудита за период"""
        query = """
        SELECT 
            COUNT(*) AS total_actions,
            COUNT(DISTINCT user_id) AS unique_users,
            COUNT(DISTINCT action) AS unique_actions,
            category,
            COUNT(*) AS category_count
        FROM audit_log
        WHERE created_at > NOW() - INTERVAL '%s days'
        GROUP BY category
        ORDER BY category_count DESC;
        """
        return self._execute_query(query, (days,))
    
    def export_audit_to_csv(self, filepath: str,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None):
        """Экспорт журнала аудита в CSV"""
        import csv
        
        query = """
        SELECT username, action, category, details, ip_address, created_at
        FROM audit_log
        WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= %s"
            params.append(end_date)
        
        query += " ORDER BY created_at DESC"
        
        rows = self._execute_query(query, tuple(params))
        
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Пользователь", "Действие", "Категория", 
                           "Детали", "IP", "Дата"])
            for row in rows:
                writer.writerow([
                    row["username"], row["action"], row["category"],
                    row["details"], row["ip_address"], row["created_at"]
                ])
    
    def _execute_query(self, query: str, params=None) -> List[Dict]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]


def audit_decorator(logger: AuditLogger):
    """Декоратор для автоматического логирования методов"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            username = kwargs.get("username", "unknown")
            user_id = kwargs.get("user_id")
            
            try:
                result = func(*args, **kwargs)
                logger.log_action(
                    user_id=user_id,
                    username=username,
                    action=f"{func.__name__}_success",
                    category=func.__module__
                )
                return result
            except Exception as e:
                logger.log_action(
                    user_id=user_id,
                    username=username,
                    action=f"{func.__name__}_error",
                    category=func.__module__,
                    details=str(e),
                    level="ERROR"
                )
                raise
        return wrapper
    return decorator
```

#### Часть 2. GUI-панель аудита

2. Создать форму `audit_panel.ui` и приложение `audit_app.py`:

Требования к интерфейсу:
- Фильтры: пользователь, категория, дата с — по, действие
- Таблица журнала аудита
- Статистика: общее количество, уникальные пользователи, по категориям
- Кнопка «Экспорт в CSV»
- Кнопка «Очистить старые записи» (старше N дней)
- Автообновление каждые 10 секунд

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Логир��вание в файлы (audit.log, audit_errors.log) | 4,00 |
| Логирование в БД (таблица audit_log) | 5,00 |
| Специальные методы логирования (вход, заказ, пользователь) | 5,00 |
| Фильтрация журнала аудита | 4,00 |
| Статистика аудита | 3,00 |
| Экспорт в CSV | 3,00 |
| GUI-панель с фильтрами | 3,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Таблица `audit_log` (создаётся автоматически при инициализации)
- Таблица `users` из инвариантной части

### Инструкция для администратора ЦПДЭ

1. Убедиться, что PostgreSQL запущен.
2. Проверить наличие директории `logs/`.

### Инструкция для технического эксперта

1. Подготовить директорию `logs/` для файлов журналов.
2. Проверить доступность psycopg2.
