# ВАРИАНТ 22: Разработка модуля резервного копирования и восстановления данных

---

## Задание

Разработать модуль автоматического резервного копирования и восстановления данных с графическим интерфейсом и планировщиком задач.

### Цель

Оценка умения осуществлять администрирование отдельных компонент серверов и обеспечивать функционирование информационной системы.

### Исходные данные

База данных PostgreSQL содержит таблицы из инвариантной части: `users`, `notes`, `customer`, `product`, `customer_order`, `order_detail`.

### Требования к выполнению

#### Часть 1. Модуль резервного копирования

1. Создать модуль `backup_system.py`:

```python
import subprocess
import os
import shutil
import json
import gzip
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import psycopg2

class BackupType(Enum):
    """Типы резервного копирования"""
    FULL = "full"           # Полное
    INCREMENTAL = "incremental"  # Инкрементное
    DATABASE_ONLY = "database"   # Только БД

class BackupStatus(Enum):
    """Статус бэкапа"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BackupInfo:
    """Информация о резервной копии"""
    id: int
    filename: str
    filepath: str
    backup_type: BackupType
    status: BackupStatus
    size_mb: float
    created_at: datetime
    record_count: int
    checksum: str
    description: str = ""

class BackupManager:
    """Управление резервным копированием"""
    
    def __init__(self, db_params: dict, backup_dir: str = "backups"):
        self.db_params = db_params
        self.backup_dir = backup_dir
        self.history_file = os.path.join(backup_dir, "backup_history.json")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Создание таблицы истории в БД
        self._init_history_table()
    
    def create_backup(self, backup_type: BackupType = BackupType.FULL,
                       description: str = "") -> BackupInfo:
        """Создание резервной копии"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{backup_type.value}_{timestamp}.sql.gz"
        filepath = os.path.join(self.backup_dir, filename)
        
        try:
            # Создание бэкапа через pg_dump
            cmd = [
                "pg_dump",
                "-h", self.db_params.get("host", "localhost"),
                "-p", str(self.db_params.get("port", 5432)),
                "-U", self.db_params.get("user", "postgres"),
                "-d", self.db_params.get("dbname", "demo_exam"),
                "-F", "p",  # plain text format
                "--inserts"  # INSERT instead of COPY
            ]
            
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                env={**os.environ, "PGPASSWORD": self.db_params.get("password", "")}
            )
            
            if result.returncode != 0:
                raise Exception(f"pg_dump error: {result.stderr}")
            
            # Сжатие gzip
            with open(filepath.replace(".gz", "tmp.sql"), "w", encoding="utf-8") as f:
                f.write(result.stdout)
            
            with open(filepath.replace(".gz", "tmp.sql"), "rb") as f_in:
                with gzip.open(filepath, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(filepath.replace(".gz", "tmp.sql"))
            
            # Вычисление checksum
            checksum = self._calculate_checksum(filepath)
            
            # Подсчёт записей
            record_count = self._count_records()
            
            # Создание записи в истории
            backup_info = BackupInfo(
                id=self._get_next_id(),
                filename=filename,
                filepath=filepath,
                backup_type=backup_type,
                status=BackupStatus.COMPLETED,
                size_mb=round(os.path.getsize(filepath) / 1024 / 1024, 2),
                created_at=datetime.now(),
                record_count=record_count,
                checksum=checksum,
                description=description
            )
            
            self._save_history_entry(backup_info)
            return backup_info
            
        except Exception as e:
            # Удаление частично созданного файла
            if os.path.exists(filepath):
                os.remove(filepath)
            raise Exception(f"Ошибка создания бэкапа: {str(e)}")
    
    def restore_backup(self, backup_info: BackupInfo) -> bool:
        """Восстановление из резервной копии"""
        if not os.path.exists(backup_info.filepath):
            raise Exception(f"Файл бэкапа не найден: {backup_info.filepath}")
        
        # Проверка checksum
        current_checksum = self._calculate_checksum(backup_info.filepath)
        if current_checksum != backup_info.checksum:
            raise Exception("Checksum не совпадает! Файл повреждён.")
        
        try:
            # Распаковка
            tmp_file = backup_info.filepath + ".tmp.sql"
            with gzip.open(backup_info.filepath, "rb") as f_in:
                with open(tmp_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Восстановление через psql
            cmd = [
                "psql",
                "-h", self.db_params.get("host", "localhost"),
                "-p", str(self.db_params.get("port", 5432)),
                "-U", self.db_params.get("user", "postgres"),
                "-d", self.db_params.get("dbname", "demo_exam"),
                "-f", tmp_file
            ]
            
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                env={**os.environ, "PGPASSWORD": self.db_params.get("password", "")}
            )
            
            os.remove(tmp_file)
            
            if result.returncode != 0:
                raise Exception(f"psql error: {result.stderr}")
            
            return True
            
        except Exception as e:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            raise Exception(f"Ошибка восстановления: {str(e)}")
    
    def delete_backup(self, backup_info: BackupInfo) -> bool:
        """Удаление резервной копии"""
        try:
            if os.path.exists(backup_info.filepath):
                os.remove(backup_info.filepath)
            self._remove_history_entry(backup_info.id)
            return True
        except Exception:
            return False
    
    def list_backups(self, backup_type: Optional[BackupType] = None,
                      limit: int = 20) -> List[BackupInfo]:
        """Список резервных копий"""
        history = self._load_history()
        
        if backup_type:
            history = [b for b in history if b["backup_type"] == backup_type.value]
        
        # Сортировка по дате (новые первые)
        history.sort(key=lambda x: x["created_at"], reverse=True)
        
        backups = []
        for entry in history[:limit]:
            backups.append(BackupInfo(
                id=entry["id"],
                filename=entry["filename"],
                filepath=entry["filepath"],
                backup_type=BackupType(entry["backup_type"]),
                status=BackupStatus(entry["status"]),
                size_mb=entry["size_mb"],
                created_at=datetime.fromisoformat(entry["created_at"]),
                record_count=entry["record_count"],
                checksum=entry["checksum"],
                description=entry.get("description", "")
            ))
        
        return backups
    
    def schedule_backup(self, interval_hours: int = 24,
                         backup_type: BackupType = BackupType.FULL,
                         max_backups: int = 30):
        """Настройка автоматического резервного копирования"""
        schedule_config = {
            "enabled": True,
            "interval_hours": interval_hours,
            "backup_type": backup_type.value,
            "max_backups": max_backups,
            "last_run": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        config_file = os.path.join(self.backup_dir, "schedule.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(schedule_config, f, ensure_ascii=False, indent=2)
        
        # Запуск фоновой задачи
        self._start_scheduler(schedule_config)
    
    def get_backup_statistics(self) -> Dict:
        """Статистика резервного копирования"""
        history = self._load_history()
        
        total_size = sum(b["size_mb"] for b in history)
        total_records = sum(b["record_count"] for b in history)
        
        by_type = {}
        for b in history:
            bt = b["backup_type"]
            if bt not in by_type:
                by_type[bt] = {"count": 0, "size_mb": 0}
            by_type[bt]["count"] += 1
            by_type[bt]["size_mb"] += b["size_mb"]
        
        return {
            "total_backups": len(history),
            "total_size_mb": round(total_size, 2),
            "total_records": total_records,
            "by_type": by_type,
            "last_backup": history[0]["created_at"] if history else None,
            "oldest_backup": history[-1]["created_at"] if history else None
        }
    
    def _init_history_table(self):
        """Инициализация таблицы истории в БД"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS backup_history (
                            id SERIAL PRIMARY KEY,
                            filename VARCHAR(200) NOT NULL,
                            backup_type VARCHAR(20) NOT NULL,
                            status VARCHAR(20) NOT NULL,
                            size_mb DECIMAL(10, 2),
                            record_count INTEGER,
                            checksum VARCHAR(32),
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    conn.commit()
        except Exception:
            pass
    
    def _save_history_entry(self, info: BackupInfo):
        """Сохранение записи в историю"""
        entry = {
            "id": info.id,
            "filename": info.filename,
            "filepath": info.filepath,
            "backup_type": info.backup_type.value,
            "status": info.status.value,
            "size_mb": info.size_mb,
            "created_at": info.created_at.isoformat(),
            "record_count": info.record_count,
            "checksum": info.checksum,
            "description": info.description
        }
        
        history = self._load_history()
        history.append(entry)
        self._save_history(history)
        
        # Запись в БД
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO backup_history 
                           (filename, backup_type, status, size_mb, 
                            record_count, checksum, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (info.filename, info.backup_type.value, 
                         info.status.value, info.size_mb,
                         info.record_count, info.checksum,
                         info.created_at)
                    )
                    conn.commit()
        except Exception:
            pass
    
    def _load_history(self) -> List[Dict]:
        if not os.path.exists(self.history_file):
            return []
        with open(self.history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save_history(self, history: List[Dict]):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def _remove_history_entry(self, backup_id: int):
        history = self._load_history()
        history = [b for b in history if b["id"] != backup_id]
        self._save_history(history)
    
    def _get_next_id(self) -> int:
        history = self._load_history()
        return max([b["id"] for b in history], default=0) + 1
    
    def _calculate_checksum(self, filepath: str) -> str:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _count_records(self) -> int:
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM customer_order"
                    )
                    return cur.fetchone()[0]
        except Exception:
            return 0
    
    def _start_scheduler(self, config: Dict):
        """Запуск планировщика бэкапов в фоне"""
        def scheduler_task():
            while config.get("enabled", False):
                last_run = datetime.fromisoformat(config["last_run"])
                if (datetime.now() - last_run).total_seconds() >= config["interval_hours"] * 3600:
                    try:
                        manager = BackupManager(self.db_params, self.backup_dir)
                        manager.create_backup(
                            BackupType(config["backup_type"])
                        )
                        config["last_run"] = datetime.now().isoformat()
                        
                        # Очистка старых бэкапов
                        history = self._load_history()
                        if len(history) > config["max_backups"]:
                            history = history[-config["max_backups"]:]
                            self._save_history(history)
                    except Exception as e:
                        pass
                
                time.sleep(300)  # Проверка каждые 5 минут
        
        thread = threading.Thread(target=scheduler_task, daemon=True)
        thread.start()
```

#### Часть 2. GUI-менеджер бэкапов

2. Создать форму `backup_manager.ui` и приложение `backup_manager_app.py`:

Требования к интерфейсу:
- Кнопка «Создать полный бэкап»
- Кнопка «Создать инкрементный бэкап»
- Таблица бэкапов (имя, тип, размер, дата, статус)
- Кнопка «Восстановить» для выбранного бэкапа
- Кнопка «Удалить»
- Кнопка «Проверить целостность» (checksum)
- Статистика: всего бэкапов, общий размер, последний бэкап
- Настройка расписания (интервал, макс. кол-во)
- Лог операций

#### Часть 3. API для бэкапов

3. Создать Flask-маршруты `api/backup_routes.py`:

```python
from flask import Blueprint, request, jsonify
from backup_system import BackupManager, BackupType, BackupStatus

backup_bp = Blueprint("backup", __name__)
manager = BackupManager(
    {"dbname": "demo_exam", "user": "postgres", "host": "localhost"}
)

@backup_bp.route("/api/backup/create", methods=["POST"])
def create_backup():
    """Создание бэкапа"""
    data = request.get_json()
    backup_type = data.get("type", "full")
    description = data.get("description", "")
    
    try:
        info = manager.create_backup(
            BackupType(backup_type), description
        )
        return jsonify({
            "id": info.id,
            "filename": info.filename,
            "size_mb": info.size_mb,
            "status": info.status.value
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@backup_bp.route("/api/backup/list", methods=["GET"])
def list_backups():
    """Список бэкапов"""
    backups = manager.list_backups()
    return jsonify([{
        "id": b.id,
        "filename": b.filename,
        "type": b.backup_type.value,
        "status": b.status.value,
        "size_mb": b.size_mb,
        "created_at": b.created_at.isoformat(),
        "record_count": b.record_count
    } for b in backups]), 200

@backup_bp.route("/api/backup/stats", methods=["GET"])
def get_stats():
    """Статистика бэкапов"""
    stats = manager.get_backup_statistics()
    return jsonify(stats), 200
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Создание бэкапа через pg_dump + gzip | 5,00 |
| Восстановление из бэкапа с проверкой checksum | 5,00 |
| Список и удаление бэкапов | 4,00 |
| Статистика резервного копирования | 3,00 |
| Планировщик автоматических бэкапов | 4,00 |
| Таблица истории в БД | 3,00 |
| Flask API для бэкапов | 3,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Утилиты `pg_dump` и `psql` в PATH
- База данных PostgreSQL

### Инструкция для администратора ЦПДЭ

1. Убедиться, что `pg_dump` и `psql` доступны в PATH.
2. Подготовить директорию `backups/`.

### Инструкция для технического эксперта

1. Проверить доступность `pg_dump` и `psql`.
2. Подготовить базу данных.
