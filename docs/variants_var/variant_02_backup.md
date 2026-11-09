# ВАРИАНТ 02: Резервное копирование и восстановление базы данных

---

## Задание

Разработать модуль резервного копирования и восстановления базы данных PostgreSQL с графическим интерфейсом.

### Цель

Оценка умения обеспечивать функционирование информационной системы, выполнять административные операции по поддержке работоспособности БД.

### Исходные данные

База данных PostgreSQL содержит таблицы из инвариантной части задания: `users`, `notes`, `customer`, `product`, `customer_order`.

### Требования к выполнению

#### Часть 1. Модуль резервного копирования (Python + subprocess)

1. Создать модуль `backup_manager.py`:

```python
import subprocess
import os
from datetime import datetime

class BackupManager:
    """Модуль резервного копирования и восстановления БД PostgreSQL"""
    
    def __init__(self, db_name, db_user, db_host="localhost", db_port=5432):
        self.db_name = db_name
        self.db_user = db_user
        self.db_host = db_host
        self.db_port = db_port
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self):
        """Создать резервную копию базы данных"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"{self.db_name}_{timestamp}.sql")
        
        try:
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", self.db_name,
                "-f", backup_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Ошибка резервного копирования: {result.stderr}")
            return backup_file
        except Exception as e:
            raise Exception(f"Не удалось создать резервную копию: {str(e)}")
    
    def restore_backup(self, backup_file):
        """Восстановить базу данных из резервной копии"""
        if not os.path.exists(backup_file):
            raise Exception(f"Файл резервной копии не найден: {backup_file}")
        
        try:
            cmd = [
                "psql",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", self.db_name,
                "-f", backup_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Ошибка восстановления: {result.stderr}")
        except Exception as e:
            raise Exception(f"Не удалось восстановить БД: {str(e)}")
    
    def list_backups(self):
        """Получить список всех резервных копий"""
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith(".sql"):
                filepath = os.path.join(self.backup_dir, filename)
                backups.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size_mb": round(os.path.getsize(filepath) / 1024 / 1024, 2),
                    "created": datetime.fromtimestamp(
                        os.path.getctime(filepath)
                    ).strftime("%d.%m.%Y %H:%M")
                })
        return sorted(backups, key=lambda x: x["created"], reverse=True)
```

#### Часть 2. GUI-приложение (PyQt6)

2. Создать форму `backup_manager.ui` и загрузчик `backup_app.py`:

Требования к интерфейсу:
- Кнопка «Создать резервную копию»
- Таблица со списком существующих бэкапов (имя, размер, дата)
- Кнопка «Восстановить» для выбранного бэкапа
- Кнопка «Удалить» для выбранного бэкапа
- Поля ввода параметров подключения к БД (хост, порт, пользователь, имя БД)
- Область логов для отображения хода выполнения операций

#### Часть 3. Автоматизация бэкапов (расписание)

3. Создать модуль `scheduled_backup.py`:

```python
import schedule
import time
from backup_manager import BackupManager

def scheduled_backup_task():
    """Ежедневное резервное копирование в 02:00"""
    manager = BackupManager(
        db_name="demo_exam",
        db_user="postgres"
    )
    try:
        backup_file = manager.create_backup()
        print(f"[{datetime.now()}] Резервная копия создана: {backup_file}")
    except Exception as e:
        print(f"[{datetime.now()}] Ошибка: {e}")

# Настройка расписания
schedule.every().day.at("02:00").do(scheduled_backup_task)

def run_scheduler():
    """Запуск планировщика"""
    print("Планировщик бэкапов запущен...")
    while True:
        schedule.run_pending()
        time.sleep(60)
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Реализовано создание резервной копии (pg_dump) | 6,00 |
| Реализовано восстановление из резервной копии (psql) | 5,00 |
| Реализован список бэкапов с информацией о файлах | 4,00 |
| Разработан GUI с Qt Designer | 5,00 |
| Реализовано расписание автоматических бэкапов | 3,00 |
| Обработка исключений, комментарии, именование | 2,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- База данных PostgreSQL с таблицами из инвариантной части
- Утилита `pg_dump` / `psql` в PATH

### Инструкция для администратора ЦПДЭ

1. Убедиться, что PostgreSQL запущен и доступен.
2. Убедиться, что утилиты `pg_dump` и `psql` доступны в PATH.
3. Подготовить базу данных с тестовыми данными.

### Инструкция для технического эксперта

1. Настроить PostgreSQL с базой данных `demo_exam`.
2. Убедиться, что пользователь `postgres` имеет права на `pg_dump` и `psql`.
3. Проверить доступность директории `backups` для записи.
