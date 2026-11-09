# ВАРИАНТ 06: Развёртывание и конфигурирование ИС на сервере

---

## Задание

Разработать скрипты автоматизации развёртывания информационной системы на сервере с конфигурацией PostgreSQL, Flask-сервера и создание конфигурационного файла.

### Цель

Оценка умения организовывать заданную интеграцию модулей в программные средства на базе имеющейся архитектуры.

### Исходные данные

Проект ИС имеет следующую структуру:
```
project/
├── src/
│   ├── main.py          # PyQt6 приложение
│   └── database.py      # Подключение к БД
├── api/
│   ├── main.py          # Flask API
│   └── routes.py        # Маршруты
├── config/
│   └── settings.py      # Конфигурация
├── requirements.txt
└── docker-compose.yml   # (не создан, нужно создать)
```

### Требования к выполнению

#### Часть 1. Конфигурационный модуль

1. Создать модуль `deploy_config.py`:

```python
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class DatabaseConfig:
    """Конфигурация PostgreSQL"""
    host: str = "localhost"
    port: int = 5432
    dbname: str = "demo_exam"
    user: str = "postgres"
    password: str = "postgres"
    
    def get_connection_string(self) -> str:
        return (f"postgresql://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.dbname}")

@dataclass
class ApiConfig:
    """Конфигурация Flask API"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    secret_key: str = "change-me-in-production"

@dataclass
class AppConfig:
    """Общая конфигурация приложения"""
    database: DatabaseConfig = None
    api: ApiConfig = None
    log_level: str = "INFO"
    log_file: str = "app.log"
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.api is None:
            self.api = ApiConfig()

class DeployConfigManager:
    """Управление конфигурацией развёртывания"""
    
    CONFIG_FILE = "deploy_config.json"
    
    def __init__(self):
        self.config = AppConfig()
    
    def load(self, filepath: Optional[str] = None):
        """Загрузка конфигурации из JSON-файла"""
        path = filepath or self.CONFIG_FILE
        if not os.path.exists(path):
            raise FileNotFoundError(f"Файл конфигурации не найден: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.config.database = DatabaseConfig(**data.get("database", {}))
        self.config.api = ApiConfig(**data.get("api", {}))
        self.config.log_level = data.get("log_level", "INFO")
        self.config.log_file = data.get("log_file", "app.log")
    
    def save(self, filepath: Optional[str] = None):
        """Сохранение конфигурации в JSON-файл"""
        path = filepath or self.CONFIG_FILE
        data = asdict(self.config)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def generate_docker_compose(self, filepath: str = "docker-compose.yml"):
        """Генерация docker-compose.yml для развёртывания"""
        db = self.config.database
        api = self.config.api
        
        compose = f"""version: '3.8'

services:
  postgres:
    image: postgres:14
    container_name: demo_db
    environment:
      POSTGRES_DB: {db.dbname}
      POSTGRES_USER: {db.user}
      POSTGRES_PASSWORD: {db.password}
    ports:
      - "{db.port}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {db.user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: ./api
    container_name: demo_api
    ports:
      - "{api.port}:{api.port}"
    environment:
      DATABASE_URL: {db.get_connection_string().replace('postgresql://', 'postgresql+psycopg2://')}
      FLASK_ENV: {'development' if api.debug else 'production'}
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  postgres_data:
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(compose)
    
    def generate_env_file(self, filepath: str = ".env"):
        """Генерация файла .env"""
        db = self.config.database
        api = self.config.api
        
        env_content = f"""# Конфигурация базы данных
DATABASE_HOST={db.host}
DATABASE_PORT={db.port}
DATABASE_NAME={db.dbname}
DATABASE_USER={db.user}
DATABASE_PASSWORD={db.password}

# Конфигурация API
API_HOST={api.host}
API_PORT={api.port}
API_SECRET_KEY={api.secret_key}
API_DEBUG={'true' if api.debug else 'false'}

# Логирование
LOG_LEVEL={self.config.log_level}
LOG_FILE={self.config.log_file}
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(env_content)
    
    def validate_config(self) -> list:
        """Валидация конфигурации"""
        errors = []
        db = self.config.database
        api = self.config.api
        
        if not (1024 <= db.port <= 65535):
            errors.append(f"Некорректный порт БД: {db.port}")
        if not (1024 <= api.port <= 65535):
            errors.append(f"Некорректный порт API: {api.port}")
        if not db.dbname:
            errors.append("Имя базы данных не задано")
        if not db.user:
            errors.append("Пользователь БД не задан")
        if api.debug and api.secret_key == "change-me-in-production":
            errors.append("В production режиме необходимо изменить secret_key")
        
        return errors
```

#### Часть 2. Скрипт развёртывания

2. Создать скрипт `deploy.py`:

```python
import subprocess
import sys
from deploy_config import DeployConfigManager

class DeployScript:
    """Автоматизация развёртывания ИС"""
    
    def __init__(self, config_manager: DeployConfigManager):
        self.config = config_manager
    
    def check_dependencies(self) -> dict:
        """Проверка наличия необходимых зависимостей"""
        results = {}
        
        checks = {
            "Python": ["python", "--version"],
            "pip": ["pip", "--version"],
            "PostgreSQL": ["psql", "--version"],
        }
        
        for name, cmd in checks.items():
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=5
                )
                results[name] = {
                    "installed": result.returncode == 0,
                    "version": result.stdout.strip()
                }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                results[name] = {"installed": False, "version": "Не установлено"}
        
        return results
    
    def install_python_packages(self):
        """Установка Python-пакетов из requirements.txt"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise Exception(result.stderr)
            return True
        except Exception as e:
            raise Exception(f"Ошибка установки пакетов: {str(e)}")
    
    def run_migrations(self):
        """Применение SQL-миграций"""
        migration_files = [
            "migrations/001_initial_schema.sql",
            "migrations/002_seed_data.sql"
        ]
        for migration in migration_files:
            if not os.path.exists(migration):
                continue
            try:
                subprocess.run(
                    ["psql", "-f", migration],
                    check=True, capture_output=True
                )
                print(f"Миграция применена: {migration}")
            except subprocess.CalledProcessError as e:
                print(f"Ошибка миграции {migration}: {e.stderr}")
    
    def deploy(self):
        """Полный цикл развёртывания"""
        print("=== Проверка зависимостей ===")
        deps = self.check_dependencies()
        for name, info in deps.items():
            status = "✓" if info["installed"] else "✗"
            print(f"  {status} {name}: {info['version']}")
        
        print("\n=== Валидация конфигурации ===")
        errors = self.config.validate_config()
        if errors:
            for error in errors:
                print(f"  ✗ {error}")
            raise Exception("Обнаружены ошибки конфигурации")
        print("  ✓ Конфигурация корректна")
        
        print("\n=== Генерация файлов развёртывания ===")
        self.config.generate_docker_compose()
        self.config.generate_env_file()
        print("  ✓ docker-compose.yml создан")
        print("  ✓ .env создан")
        
        print("\n=== Развёртывание завершено ===")
```

#### Часть 3. GUI для управления развёртыванием

3. Создать форму `deploy_ui.ui` и приложение `deploy_app.py` с кнопками:
   - «Проверить зависимости»
   - «Сгенерировать конфигурацию»
   - «Установить пакеты»
   - «Применить миграции»
   - «Полное развёртывание»
   - Область вывода логов

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Реализован модуль конфигурации (DataClass) | 5,00 |
| Генерация docker-compose.yml | 5,00 |
| Генерация .env файла | 3,00 |
| Валидация конфигурации | 3,00 |
| Скрипт проверки зависимостей | 4,00 |
| GUI для управления развёртыванием | 3,00 |
| Обработка исключений, комментарии | 2,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Файл `requirements.txt` проекта
- SQL-файлы миграций

### Инструкция для администратора ЦПДЭ

1. Подготовить структуру проекта.
2. Убедиться, что pip и Python установлены.

### Инстру��ция для технического эксперта

1. Проверить доступность Docker (опционально).
2. Подготовить файл `requirements.txt`.
