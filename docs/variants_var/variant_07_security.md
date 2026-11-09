# ВАРИАНТ 07: Обеспечение информационной безопасности ИС

---

## Задание

Разработать модуль обеспечения информационной безопасности: хеширование паролей, генерация токенов, проверка сложности пароля, журналирование попыток доступа.

### Цель

Оценка умения разрабатывать подсистемы безопасности информационной системы в соответствии с техническим заданием.

### Исходные данные

Таблица `users` в PostgreSQL:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('Администратор', 'Пользователь')),
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP DEFAULT NULL
);
```

### Требования к выполнению

#### Часть 1. Модуль безопасности

1. Создать модуль `security_module.py`:

```python
import hashlib
import secrets
import re
import time
from datetime import datetime, timedelta
from typing import Tuple, Optional
import psycopg2

class SecurityManager:
    """Модуль обеспечения информационной безопасности"""
    
    LOCKOUT_DURATION = timedelta(minutes=30)
    MIN_PASSWORD_LENGTH = 8
    HASH_ALGORITHM = "sha256"
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Хеширование пароля с солью
        Возвращает: (хеш, соль)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{salt}{password}"
        password_hash = hashlib.scrypt(
            combined.encode("utf-8"),
            salt=bytes.fromhex(salt),
            n=16384,
            r=8,
            p=1
        ).hex()
        
        return password_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Проверка пароля по хешу и соли"""
        computed_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)
    
    def validate_password_strength(self, password: str) -> Tuple[bool, list]:
        """
        Проверка сложности пароля
        Возвращает: (корректен, список замечаний)
        """
        issues = []
        
        if len(password) < self.MIN_PASSWORD_LENGTH:
            issues.append(
                f"Пароль должен содержать не менее {self.MIN_PASSWORD_LENGTH} символов"
            )
        if not re.search(r"[A-Z]", password):
            issues.append("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", password):
            issues.append("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"\d", password):
            issues.append("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            issues.append("Пароль должен содержать хотя бы один спецсимвол")
        
        return len(issues) == 0, issues
    
    def generate_api_token(self) -> str:
        """Генерация токена API"""
        return secrets.token_urlsafe(32)
    
    def check_lockout(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Проверка блокировки пользователя
        Возвращает: (заблокирован, причина)
        """
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT is_blocked, locked_until FROM users WHERE id = %s",
                        (user_id,)
                    )
                    row = cur.fetchone()
                    if not row:
                        return False, None
                    
                    is_blocked, locked_until = row
                    
                    if is_blocked and locked_until:
                        if datetime.now() < locked_until:
                            remaining = locked_until - datetime.now()
                            minutes = int(remaining.total_seconds() / 60) + 1
                            return True, f"Учётная запись заблокирована. Осталось: {minutes} мин."
                        else:
                            # Время блокировки истекло — разблокировать
                            self._unlock_user(user_id)
                            return False, None
                    
                    return False, None
        except Exception:
            return False, None
    
    def record_failed_attempt(self, user_id: int) -> Tuple[bool, int]:
        """
        Фиксация неудачной попытки входа
        Возвращает: (заблокирован, количество попыток)
        """
        max_attempts = 3
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT failed_attempts FROM users WHERE id = %s",
                        (user_id,)
                    )
                    row = cur.fetchone()
                    attempts = row[0] + 1 if row else 1
                    
                    cur.execute(
                        """UPDATE users 
                           SET failed_attempts = %s,
                               is_blocked = CASE WHEN %s >= %s THEN TRUE ELSE FALSE END,
                               locked_until = CASE 
                                   WHEN %s >= %s THEN NOW() + INTERVAL '30 minutes'
                                   ELSE NULL END
                           WHERE id = %s""",
                        (attempts, attempts, max_attempts, attempts, max_attempts, user_id)
                    )
                    conn.commit()
                    
                    return attempts >= max_attempts, attempts
        except Exception:
            conn.rollback()
            return False, 0
    
    def _unlock_user(self, user_id: int):
        """Разблокировка пользователя"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE users 
                           SET is_blocked = FALSE, 
                               failed_attempts = 0, 
                               locked_until = NULL
                           WHERE id = %s""",
                        (user_id,)
                    )
                    conn.commit()
        except Exception:
            conn.rollback()
    
    def get_security_audit_log(self, hours: int = 24) -> list:
        """Получить журнал событий безопасности"""
        query = """
        SELECT 
            u.login,
            a.action,
            a.ip_address,
            a.details,
            a.created_at
        FROM security_audit a
        JOIN users u ON a.user_id = u.id
        WHERE a.created_at > NOW() - INTERVAL '%s hours'
        ORDER BY a.created_at DESC;
        """
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (hours,))
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception:
            return []
```

#### Часть 2. GUI-панель безопасности

2. Создать форму `security_panel.ui` и приложение `security_app.py`:

Требования к интерфейсу:
- Форма смены пароля с проверкой сложности в реальном времени
- Индикатор сложности пароля (полоса прогресса + цвет)
- Таблица журнала событий безопасности
- Кнопка «Сгенерировать токен API»
- Кнопка «Очистить журнал»
- Фильтр по дате

#### Часть 3. Таблица аудита

3. Создать SQL-миграцию `migrations/003_security_audit.sql`:

```sql
-- Таблица аудита безопасности
CREATE TABLE IF NOT EXISTS security_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    details TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индекс для быстрого поиска
CREATE INDEX idx_security_audit_created ON security_audit(created_at);
CREATE INDEX idx_security_audit_user ON security_audit(user_id);

-- Триггер для автоматической записи
CREATE OR REPLACE FUNCTION log_security_action()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO security_audit (user_id, action, details)
    VALUES (NEW.id, NEW.action, NEW.details);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_security_audit
    AFTER INSERT ON security_audit
    FOR EACH ROW EXECUTE FUNCTION log_security_action();
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Хеширование паролей (scrypt) с солью | 5,00 |
| Проверка сложности пароля с подсказками | 4,00 |
| Механизм блокировки учётной записи | 5,00 |
| Генерация токенов API | 3,00 |
| GUI с индикатором сложности пароля | 4,00 |
| Таблица аудита и журнал событий | 3,00 |
| Обработка исключений, комментарии | 1,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Таблица `users` с полями `failed_attempts`, `locked_until`
- SQL-миграция аудита

### Инструкция для администратора ЦПДЭ

1. Убедиться, что таблица `users` имеет дополнительные поля безопасности.
2. Убедиться, что криптографические библиотеки доступны.

### Инструкция для технического эксперта

1. Подготовить таблицу `users` с полями блокировки.
2. Проверить наличие `hashlib` и `secrets` в стандартной библиотеке Python.
