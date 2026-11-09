# ВАРИАНТ 10: Миграция и обновление схемы базы данных

---

## Задание

Разработать систему управления миграциями базы данных PostgreSQL для безопасного обновления схемы БД.

### Цель

Оценка умения осуществлять администрирование отдельных компонент серверов и выявлять технические проблемы при эксплуатации БД.

### Исходные данные

Текущая схема БД:

```sql
-- Текущая версия схемы (v1)
CREATE TABLE customer (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    inn VARCHAR(20),
    address VARCHAR(300),
    phone VARCHAR(20),
    customer_type VARCHAR(50)
);

CREATE TABLE product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE,
    price DECIMAL(10, 2)
);
```

Требуется обновить схему до v2 с добавлением новых полей и таблиц.

### Требования к выполнению

#### Часть 1. Система миграций

1. Создать модуль `migration_manager.py`:

```python
import os
import json
import hashlib
from typing import List, Dict, Optional
from datetime import datetime
import psycopg2

class MigrationManager:
    """Система управления миграциями БД"""
    
    MIGRATIONS_DIR = "migrations"
    HISTORY_TABLE = "_migration_history"
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def get_current_version(self) -> int:
        """Получить текущую версию схемы БД"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT MAX(version) FROM {self.HISTORY_TABLE}"
                    )
                    result = cur.fetchone()[0]
                    return result if result else 0
        except psycopg2.ProgrammingError:
            return 0
    
    def get_available_migrations(self) -> List[Dict]:
        """Получить список доступных миграций"""
        migrations = []
        for filename in sorted(os.listdir(self.MIGRATIONS_DIR)):
            if filename.endswith(".sql") and not filename.startswith("_"):
                filepath = os.path.join(self.MIGRATIONS_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Извлечение версии из имени файла
                version = int(filename.split("_")[0])
                
                # Вычисление хеша для проверки изменений
                file_hash = hashlib.md5(
                    content.encode("utf-8")
                ).hexdigest()
                
                migrations.append({
                    "version": version,
                    "filename": filename,
                    "filepath": filepath,
                    "hash": file_hash,
                    "content": content
                })
        
        return migrations
    
    def apply_migration(self, migration: Dict) -> bool:
        """Применение одной миграции"""
        version = migration["version"]
        
        # Проверка, не применена ли уже
        if self._is_applied(version):
            print(f"Миграция v{version} уже применена")
            return True
        
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    # Начало транзакции
                    cur.execute("BEGIN")
                    
                    # Применение SQL
                    cur.execute(migration["content"])
                    
                    # Запись в историю
                    cur.execute(
                        f"""INSERT INTO {self.HISTORY_TABLE} 
                            (version, applied_at, file_hash)
                            VALUES (%s, NOW(), %s)""",
                        (version, migration["hash"])
                    )
                    
                    conn.commit()
                    print(f"✓ Миграция v{version} применена")
                    return True
                    
        except Exception as e:
            conn.rollback()
            print(f"✗ Ошибка применения миграции v{version}: {e}")
            raise
    
    def rollback_migration(self, version: int) -> bool:
        """Откат миграции до указанной версии"""
        current = self.get_current_version()
        
        if version >= current:
            print(f"Нельзя откатить: целевая версия >= текущей")
            return False
        
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("BEGIN")
                    
                    # Удаление записей истории
                    cur.execute(
                        f"DELETE FROM {self.HISTORY_TABLE} WHERE version > %s",
                        (version,)
                    )
                    
                    conn.commit()
                    print(f"✓ Откат до v{version} выполнен")
                    return True
                    
        except Exception as e:
            conn.rollback()
            print(f"✗ Ошибка отката: {e}")
            raise
    
    def migrate(self, target_version: Optional[int] = None) -> List[int]:
        """Применение всех доступных миграций"""
        current = self.get_current_version()
        migrations = self.get_available_migrations()
        applied = []
        
        for migration in migrations:
            if migration["version"] <= current:
                continue
            if target_version and migration["version"] > target_version:
                break
            
            self.apply_migration(migration)
            applied.append(migration["version"])
        
        return applied
    
    def generate_migration(self, name: str, sql_up: str, sql_down: str) -> str:
        """Генерация нового файла миграции"""
        current = self.get_current_version()
        version = current + 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{version:03d}_{name}_{timestamp}.sql"
        filepath = os.path.join(self.MIGRATIONS_DIR, filename)
        
        content = f"""-- Миграция v{version}: {name}
-- Создано: {timestamp}

-- UP
{sql_up}

-- DOWN
-- {sql_down}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Создан файл миграции: {filename}")
        return filepath
    
    def get_migration_status(self) -> Dict:
        """Получить статус миграций"""
        current = self.get_current_version()
        migrations = self.get_available_migrations()
        
        status = {
            "current_version": current,
            "available_count": len(migrations),
            "pending_count": 0,
            "migrations": []
        }
        
        for m in migrations:
            applied = self._is_applied(m["version"])
            if not applied:
                status["pending_count"] += 1
            status["migrations"].append({
                "version": m["version"],
                "filename": m["filename"],
                "applied": applied
            })
        
        return status
    
    def _is_applied(self, version: int) -> bool:
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT COUNT(*) FROM {self.HISTORY_TABLE} WHERE version = %s",
                        (version,)
                    )
                    return cur.fetchone()[0] > 0
        except psycopg2.ProgrammingError:
            return False
```

#### Часть 2. Примеры миграций

2. Создать SQL-файлы миграций:

`migrations/001_create_migration_history.sql`:
```sql
CREATE TABLE IF NOT EXISTS _migration_history (
    id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL UNIQUE,
    applied_at TIMESTAMP DEFAULT NOW(),
    file_hash VARCHAR(32)
);
```

`migrations/002_add_customer_fields.sql`:
```sql
-- UP: Добавление новых полей в таблицу customer
ALTER TABLE customer ADD COLUMN email VARCHAR(100);
ALTER TABLE customer ADD COLUMN contact_person VARCHAR(100);
ALTER TABLE customer ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
CREATE INDEX idx_customer_email ON customer(email);

-- DOWN: Откат
-- ALTER TABLE customer DROP COLUMN email;
-- ALTER TABLE customer DROP COLUMN contact_person;
-- ALTER TABLE customer DROP COLUMN created_at;
-- DROP INDEX idx_customer_email;
```

`migrations/003_add_order_status.sql`:
```sql
-- UP: Добавление статуса заказа
ALTER TABLE customer_order ADD COLUMN status VARCHAR(50) DEFAULT 'Новый';
ALTER TABLE customer_order ADD COLUMN completed_at TIMESTAMP;
ALTER TABLE customer_order ADD COLUMN comment TEXT;

-- Создание перечисления для статусов
CREATE TYPE order_status AS ENUM ('Новый', 'В работе', 'Завершён', 'Отменён');

-- DOWN:
-- ALTER TABLE customer_order DROP COLUMN status;
-- ALTER TABLE customer_order DROP COLUMN completed_at;
-- ALTER TABLE customer_order DROP COLUMN comment;
-- DROP TYPE order_status;
```

#### Часть 3. GUI-менеджер миграций

3. Создать форму `migration_manager.ui` и приложение `migration_app.py`:

Требования к интерфейсу:
- Отображение текущей версии БД
- Таблица доступных миграций с чекбоксами
- Кнопка «Применить все»
- Кнопка «Откат до версии»
- Предпросмотр SQL-кода миграции
- Лог применения миграций
- Кнопка «Создать новую миграцию»

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Управление версиями миграций | 5,00 |
| Применение миграций в транзакции | 5,00 |
| Откат миграций | 4,00 |
| Генерация новых файлов миграций | 4,00 |
| GUI с предпросмотром и логом | 4,00 |
| Проверка хешей для обнаружения изменений | 2,00 |
| Обработка исключений, комментарии | 1,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Папка `migrations/` с SQL-файлами
- База данных PostgreSQL

### Инструкция для администратора ЦПДЭ

1. Подготовить папку `migrations/` с SQL-файлами.
2. Убедиться, что PostgreSQL запущен.

### Инструкция для технического эксперта

1. Создать папку `migrations/` с примерами SQL-файлов.
2. Проверить доступность psycopg2.
