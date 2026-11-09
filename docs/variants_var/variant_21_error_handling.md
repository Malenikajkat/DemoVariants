# ВАРИАНТ 21: Разработка модуля обработки исключений и мониторинга ошибок

---

## Задание

Разработать централизованную систему обработки исключений, мониторинга ошибок и автоматического восстановления после сбоев.

### Цель

Оценка умения производить разработку модулей информационной системы в соответствии с техническим заданием, использовать отладку и обрабатывать исключительные ситуации.

### Исходные данные

Информационная система включает модули: авторизации, работы с БД, API, GUI.

### Требования к выполнению

#### Часть 1. Система обработки исключений

1. Создать модуль `exception_handler.py`:

```python
import traceback
import logging
import json
import os
import sys
import threading
import time
from typing import Optional, Dict, List, Callable, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import psycopg2

class ErrorSeverity(Enum):
    """Серьёзность ошибки"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Категория ошибки"""
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    API = "api"
    GUI = "gui"
    FILE = "file"
    NETWORK = "network"
    UNKNOWN = "unknown"

@dataclass
class ErrorRecord:
    """Запись об ошибке"""
    id: int
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    stack_trace: str
    module: str
    user_id: Optional[int] = None
    is_resolved: bool = False
    resolution_notes: str = ""

class CustomExceptions:
    """Пользовательские исключения для ИС"""
    
    class AppException(Exception):
        """Базовое исключение приложения"""
        def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN):
            self.category = category
            super().__init__(message)
    
    class DatabaseError(AppException):
        """Ошибка работы с БД"""
        def __init__(self, message: str):
            super().__init__(message, ErrorCategory.DATABASE)
    
    class AuthenticationError(AppException):
        """Ошибка авторизации"""
        def __init__(self, message: str):
            super().__init__(message, ErrorCategory.AUTHENTICATION)
    
    class ValidationError(AppException):
        """Ошибка валидации данных"""
        def __init__(self, message: str):
            super().__init__(message, ErrorCategory.GUI)
    
    class APIError(AppException):
        """Ошибка API"""
        def __init__(self, message: str, status_code: int = 500):
            self.status_code = status_code
            super().__init__(message, ErrorCategory.API)
    
    class FileError(AppException):
        """Ошибка работы с файлами"""
        def __init__(self, message: str):
            super().__init__(message, ErrorCategory.FILE)

class ErrorHandler:
    """Централизованный обработчик ошибок"""
    
    def __init__(self, log_dir: str = "logs", db_params: Optional[dict] = None):
        self.log_dir = log_dir
        self.db_params = db_params
        os.makedirs(log_dir, exist_ok=True)
        
        self._setup_logging()
        self._errors: List[ErrorRecord] = []
        self._error_counter = 0
        self._lock = threading.Lock()
        
        # Глобальный обработчик необработанных исключений
        self._install_global_handler()
    
    def _setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger("error_handler")
        self.logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Файл всех ошибок
        fh = logging.FileHandler(
            os.path.join(self.log_dir, "errors.log"),
            encoding="utf-8"
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Файл критических ошибок
        cfh = logging.FileHandler(
            os.path.join(self.log_dir, "critical_errors.log"),
            encoding="utf-8"
        )
        cfh.setFormatter(formatter)
        cfh.setLevel(logging.CRITICAL)
        self.logger.addHandler(cfh)
    
    def _install_global_handler(self):
        """Установка глобального обработчика"""
        def global_exception_handler(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            self.log_error(
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.UNKNOWN,
                message=f"{exc_type.__name__}: {exc_value}",
                stack_trace="".join(traceback.format_tb(exc_traceback))
            )
        
        sys.excepthook = global_exception_handler
    
    def log_error(self, severity: ErrorSeverity, category: ErrorCategory,
                   message: str, stack_trace: str = "",
                   module: str = "", user_id: Optional[int] = None) -> ErrorRecord:
        """Запись ошибки"""
        with self._lock:
            self._error_counter += 1
            error_id = self._error_counter
            
            record = ErrorRecord(
                id=error_id,
                timestamp=datetime.now(),
                severity=severity,
                category=category,
                message=message,
                stack_trace=stack_trace,
                module=module or self._get_caller_module(),
                user_id=user_id
            )
            
            self._errors.append(record)
            
            # Логирование
            log_method = getattr(self.logger, severity.value, self.logger.info)
            log_method(f"[{category.value}] {message}")
            
            # Запись в БД
            if self.db_params:
                self._save_to_db(record)
            
            return record
    
    def handle_database_error(self, error: Exception, 
                               operation: str = "") -> ErrorRecord:
        """Обработка ошибок БД с попыткой восстановления"""
        record = self.log_error(
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.DATABASE,
            message=f"DB Error ({operation}): {str(error)}",
            stack_trace=traceback.format_exc()
        )
        
        # Попытка переподключения
        self._attempt_db_recovery()
        
        return record
    
    def handle_auth_error(self, error: Exception, 
                           username: str = "") -> ErrorRecord:
        """Обработка ошибок авторизации"""
        return self.log_error(
            severity=ErrorSeverity.WARNING,
            category=ErrorCategory.AUTHENTICATION,
            message=f"Auth Error (user='{username}'): {str(error)}",
            stack_trace=traceback.format_exc()
        )
    
    def get_errors(self, severity: Optional[ErrorSeverity] = None,
                    category: Optional[ErrorCategory] = None,
                    since: Optional[datetime] = None,
                    limit: int = 100) -> List[ErrorRecord]:
        """Получение списка ошибок с фильтрацией"""
        errors = self._errors[:]
        
        if severity:
            errors = [e for e in errors if e.severity == severity]
        if category:
            errors = [e for e in errors if e.category == category]
        if since:
            errors = [e for e in errors if e.timestamp >= since]
        
        return errors[-limit:]
    
    def get_error_statistics(self, days: int = 7) -> Dict:
        """Статистика ошибок"""
        cutoff = datetime.now()
        from datetime import timedelta
        cutoff = cutoff - timedelta(days=days)
        
        recent = [e for e in self._errors if e.timestamp >= cutoff]
        
        by_severity = {}
        by_category = {}
        
        for e in recent:
            by_severity[e.severity.value] = by_severity.get(e.severity.value, 0) + 1
            by_category[e.category.value] = by_category.get(e.category.value, 0) + 1
        
        return {
            "period_days": days,
            "total_errors": len(recent),
            "by_severity": by_severity,
            "by_category": by_category,
            "critical_count": by_severity.get("critical", 0),
            "resolved_count": sum(1 for e in recent if e.is_resolved)
        }
    
    def export_errors_to_json(self, filepath: str):
        """Экспорт ошибок в JSON"""
        errors_data = []
        for e in self._errors:
            errors_data.append({
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "severity": e.severity.value,
                "category": e.category.value,
                "message": e.message,
                "stack_trace": e.stack_trace[:500],
                "module": e.module,
                "is_resolved": e.is_resolved
            })
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(errors_data, f, ensure_ascii=False, indent=2)
    
    def _save_to_db(self, record: ErrorRecord):
        """Сохранение ошибки в БД"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO error_log 
                           (severity, category, message, stack_trace, 
                            module, user_id, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
                        (
                            record.severity.value,
                            record.category.value,
                            record.message,
                            record.stack_trace[:4000],
                            record.module,
                            record.user_id
                        )
                    )
                    conn.commit()
        except Exception:
            pass  # Файловый лог работает всегда
    
    def _attempt_db_recovery(self):
        """Попытка восстановления подключения к БД"""
        if not self.db_params:
            return
        
        try:
            with psycopg2.connect(**self.db_params) as conn:
                conn.close()
            self.logger.info("Подключение к БД восстановлено")
        except Exception:
            self.logger.warning("Не удалось восстановить подключение к БД")
    
    def _get_caller_module(self) -> str:
        """Получение имени вызвавшего модуля"""
        try:
            return traceback.extract_stack()[-2].name
        except:
            return "unknown"
    
    def _execute_query(self, query: str, params=None) -> List[Dict]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]


# Глобальный обработчик ошибок для PyQt
def install_pyqt_error_handler(error_handler: ErrorHandler):
    """Установка обработчика ошибок для PyQt-приложений"""
    def qt_error_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_handler.log_error(
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.GUI,
            message=f"GUI Error: {exc_value}",
            stack_trace="".join(traceback.format_tb(exc_traceback))
        )
    
    sys.excepthook = qt_error_handler
```

#### Часть 2. GUI-панель мониторинга ошибок

2. Создать форму `error_monitor.ui` и приложение `error_monitor_app.py`:

Требования к интерфейсу:
- Фильтры: серьёзность, категория, дата
- Таблица ошибок с цветовой индикацией
- Область детального просмотра (стек-трейс)
- Кнопка «Отметить разрешённой»
- Статистика: общее кол-во, по категориям, по серьёзности
- Кнопка «Экспорт в JSON»
- Кнопка «Очистить resolved»
- Автообновление каждые 5 секунд

#### Часть 3. Декораторы обработки ошибок

3. Создать модуль `error_decorators.py`:

```python
from exception_handler import ErrorHandler, ErrorSeverity, ErrorCategory
from functools import wraps

def catch_errors(error_handler: ErrorHandler, 
                  category: ErrorCategory = ErrorCategory.UNKNOWN):
    """Декоратор для обработки ошибок в функциях"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(
                    severity=ErrorSeverity.ERROR,
                    category=category,
                    message=f"{func.__name__}(): {str(e)}",
                    stack_trace=__import__('traceback').format_exc()
                )
                raise
        return wrapper
    return decorator
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Пользовательские исключения | 4,00 |
| Централизованный обработчик ошибок | 5,00 |
| Логирование в файлы (errors.log, critical_errors.log) | 4,00 |
| Запись ошибок в БД | 3,00 |
| Глобальный обработчик исключений | 3,00 |
| Статистика и фильтрация ошибок | 3,00 |
| GUI-панель мониторинга | 3,00 |
| Экспорт ошибок в JSON | 0,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Таблица `error_log` (создаётся автоматически)
- Директория `logs/`

### Инструкция для администратора ЦПДЭ

1. Подготовить директорию `logs/`.
2. Убедиться, что PostgreSQL запущен.

### Инструкция для технического эксперта

1. Проверить доступность psycopg2.
2. Подготовить директорию для логов.
