# Демонстрационный экзамен — Стоматология «Улыбка»
## Вариант 15 | Специальность 09.02.07 | КИМ 09.02.07-5-2027

---

## О проекте

Полный проект демонстрационного экзамена, включающий все 22 варианта заданий:

### Задания 1-4 (Инвариантная часть)
- **Задание 1**: ER-диаграмма (PDF) — `task1_er_diagram/er_diagram_variant15.pdf`
- **Задание 2**: База данных PostgreSQL — `task2_db/`
- **Задание 3**: SQL-запрос для расчёта стоимости — `task3_query/`
- **Задание 4**: PyQt6-приложение с авторизацией и капчей — `src/main.py`

### Задания 5-6 (API и документация)
- **Задание 5**: API на FastAPI (GET /api/notes) — `src/api_server.py`
- **Задание 6**: Документация API — `docs/API_Documentation.md`

### Варианты 01-22 (Дополнительные модули)
Все модули находятся в папке `src/` с подробными комментариями.

---

## Архитектура проекта

```
proba/
├── ui/                          # Qt Designer файлы (Задание 4)
│   ├── login_window.ui
│   ├── admin_panel.ui
│   └── user_panel.ui
├── src/                         # Исходный код
│   ├── __init__.py              # Инициализация пакета
│   ├── main.py                  # Точка входа (PyQt6)
│   ├── database.py              # Менеджер БД
│   ├── auth_module.py           # Модуль авторизации
│   ├── captcha_module.py        # Капча-пазл
│   ├── user_manager.py          # Управление пользователями
│   ├── exceptions.py            # Пользовательские исключения
│   ├── api_server.py            # API на FastAPI (Задание 5)
│   │
│   ├── [Вариант 01] Тестирование
│   │   └── tests/test_api_cases.py, test_api_automation.py, test_gui_auth.py
│   │
│   ├── [Вариант 02] Резервное копирование
│   │   ├── backup_manager.py    # Создание и восстановление бэкапов
│   │   ├── backup_app.py        # GUI для управления бэкапами
│   │   └── scheduled_backup.py  # Автоматическое копирование по расписанию
│   │
│   ├── [Вариант 03] Мониторинг БД
│   │   ├── db_monitor.py        # Сбор метрик производительности
│   │   └── report_generator.py  # Генерация отчётов в CSV
│   │
│   ├── [Вариант 04] Документация
│   │   ├── pdf_generator.py     # Генерация PDF-документации
│   │   └── doc_collector.py     # Сбор данных для документации
│   │
│   ├── [Вариант 05] Требования
│   │   ├── requirement_analyzer.py  # Анализ требований
│   │   └── requirement_exporter.py  # Экспорт в JSON и TXT
│   │
│   ├── [Вариант 06] Развёртывание
│   │   ├── deploy_config.py     # Конфигурация и генерация docker-compose
│   │   ├── deploy.py            # Автоматизация развёртывания
│   │   └── deploy_app.py        # GUI для управления
│   │
│   ├── [Вариант 07] Безопасность
│   │   └── security_module.py   # Хеширование паролей, проверка сложности
│   │
│   ├── [Вариант 08] Оптимизация SQL
│   │   └── query_optimizer.py   # Анализ и оптимизация запросов
│   │
│   ├── [Вариант 09] Аналитика
│   │   ├── analytics_engine.py  # Аналитические запросы
│   │   └── report_exporter.py   # Экспорт отчётов
│   │
│   ├── [Вариант 10] Миграции БД
│   │   └── migration_manager.py # Управление версиями схемы БД
│   │
│   ├── [Вариант 11] Email
│   │   └── email_integration.py # Отправка email через SMTP
│   │
│   ├── [Вариант 12] Права доступа
│   │   └── access_control.py    # Ролевая модель и разрешения
│   │
│   ├── [Вариант 13] Импорт/Экспорт
│   │   └── data_io.py           # Импорт/экспорт CSV, JSON, Excel
│   │
│   ├── [Вариант 14] Автоматизация
│   │   └── procedure_caller.py  # Вызов хранимых процедур PostgreSQL
│   │
│   ├── [Вариант 15] Уведомления
│   │   └── notification_system.py # Система уведомлений
│   │
│   ├── [Вариант 16] Дашборд
│   │   └── dashboard_metrics.py # Сбор метрик для визуализации
│   │
│   ├── [Вариант 17] Логирование
│   │   └── audit_logger.py      # Журнал действий пользователей
│   │
│   ├── [Вариант 18] Поиск
│   │   └── search_engine.py     # Универсальный поиск и фильтрация
│   │
│   ├── [Вариант 19] Экспорт PDF/Excel
│   │   └── pdf_report.py        # Генерация отчётов в PDF и Excel
│   │
│   └── [Вариант 20] Кэширование
│       └── cache_manager.py     # LRU-кэш и кэширование запросов
│
├── task1_er_diagram/            # Задание 1: ER-диаграмма
├── task2_db/                    # Задание 2: База данных
├── task3_query/                 # Задание 3: SQL-запрос
├── api/                         # Задание 5: SQL для таблицы notes
├── tests/                       # Задание 1: Тесты
├── docs/                        # Документация
│   ├── API_Documentation.md     # Документация API (Задание 6)
│   └── variants_var/            # Все 22 варианта заданий
├── images/                      # Изображения для капчи
├── resources/                   # Ресурсы (стили, иконки)
├── requirements.txt             # Зависимости
└── README.md                    # Этот файл
```

---

## Требования

| Компонент | Версия |
|-----------|--------|
| Python | 3.10+ |
| PostgreSQL | 14+ |
| PyQt6 | 6.4+ |
| FastAPI | 0.100+ |
| uvicorn | 0.23+ |

---

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Создание базы данных

```bash
# Создать базу данных
psql -U postgres -c "CREATE DATABASE stomatologiya;"

# Создать таблицы
psql -U postgres -d stomatologiya -f task2_db/001_create_tables.sql

# Загрузить тестовые данные клиентов
python task2_db/import_customers.py

# Создать таблицу для API
psql -U postgres -d stomatologiya -f api/001_create_notes_table.sql
```

### 3. Запуск PyQt6-приложения (Задание 4)

```bash
python src/main.py
```

### 4. Запуск API (Задание 5)

```bash
python src/api_server.py
```

Открыть браузер:
- **Документация**: http://127.0.0.1:8000/docs
- **API**: http://127.0.0.1:8000/api/notes

---

## Тестовые пользователи

| Логин | Пароль | Роль |
|-------|--------|------|
| admin | admin123 | Администратор |
| user1 | user123 | Пользователь |
| user2 | user123 | Пользователь |

---

## Описание всех модулей

### Задание 1: ER-диаграмма
- **Файл**: `task1_er_diagram/er_diagram_variant15.pdf`
- 12 сущностей с foreign keys (user_account изолирован)

### Задание 2: База данных
- **Файлы**: `task2_db/001_create_tables.sql`, `import_customers.py`
- 13 таблиц в 3НФ

### Задание 3: SQL-запрос
- **Файл**: `task3_query/001_customer_order_cost.sql`
- Расчёт стоимости через CTE

### Задание 4: PyQt6-приложение
- **Файлы**: `src/main.py`, `src/database.py`, `src/auth_module.py`, `src/captcha_module.py`
- Авторизация с капчей-пазлом, блокировка после 3 попыток

### Задание 5: API
- **Файл**: `src/api_server.py`
- GET /api/notes с обработкой ошибок

### Задание 6: Документация API
- **Файл**: `docs/API_Documentation.md`
- Полная документация по шаблону

### Вариант 01: Тестирование
- **Файлы**: `tests/test_api_cases.py`, `test_api_automation.py`, `test_gui_auth.py`
- 5 тест-кейсов, автоматизация с pytest, тестирование GUI

### Вариант 02: Резервное копирование
- **Файлы**: `src/backup_manager.py`, `src/backup_app.py`, `src/scheduled_backup.py`
- pg_dump, восстановление, расписание

### Вариант 03: Мониторинг БД
- **Файлы**: `src/db_monitor.py`, `src/report_generator.py`
- Метрики производительности, отчёты в CSV

### Вариант 04: Документация
- **Файлы**: `src/pdf_generator.py`, `src/doc_collector.py`
- Генерация PDF-документации с reportlab

### Вариант 05: Требования
- **Файлы**: `src/requirement_analyzer.py`, `src/requirement_exporter.py`
- Анализ, граф зависимостей, валидация

### Вариант 06: Развёртывание
- **Файлы**: `src/deploy_config.py`, `src/deploy.py`, `src/deploy_app.py`
- docker-compose, .env, автоматизация

### Вариант 07: Безопасность
- **Файлы**: `src/security_module.py`
- Хеширование scrypt, проверка сложности пароля, блокировка

### Вариант 08: Оптимизация SQL
- **Файлы**: `src/query_optimizer.py`
- Индексы, EXPLAIN ANALYZE, рекомендации

### Вариант 09: Аналитика
- **Файлы**: `src/analytics_engine.py`, `src/report_exporter.py`
- 7 метрик, экспорт в CSV

### Вариант 10: Миграции БД
- **Файлы**: `src/migration_manager.py`
- Управление версиями, транзакции, откат

### Вариант 11: Email
- **Файлы**: `src/email_integration.py`
- SMTP, HTML-письма, подтверждение заказа

### Вариант 12: Права доступа
- **Файлы**: `src/access_control.py`
- Роли, разрешения, аудит

### Вариант 13: Импорт/Экспорт
- **Файлы**: `src/data_io.py`
- CSV, JSON, Excel

### Вариант 14: Автоматизация
- **Файлы**: `src/procedure_caller.py`
- Хранимые процедуры PostgreSQL

### Вариант 15: Уведомления
- **Файлы**: `src/notification_system.py`
- Каналы доставки, приоритеты

### Вариант 16: Дашборд
- **Файлы**: `src/dashboard_metrics.py`
- KPI, графики, визуализация

### Вариант 17: Логирование
- **Файлы**: `src/audit_logger.py`
- Журнал действий, экспорт в CSV

### Вариант 18: Поиск
- **Файлы**: `src/search_engine.py`
- Полнотекстовый поиск, фильтрация, пагинация

### Вариант 19: Экспорт PDF/Excel
- **Файлы**: `src/pdf_report.py`
- Отчёты с таблицами и стилями

### Вариант 20: Кэширование
- **Файлы**: `src/cache_manager.py`
- LRU-кэш, TTL, декораторы

---

## Именование элементов

Все идентификаторы отражают суть:
- `login_field` — поле логина
- `password_field` — поле пароля
- `login_button` — кнопка входа
- `captcha_widget` — виджет капчи
- `tbl_users` — таблица пользователей

---

## PyCharm: Настройка Python

Убедитесь, что PyCharm использует **Python 3.11**, а не Python 2.7:

1. **File → Settings → Project → Python Interpreter**
2. Нажмите на шестерёнку → **Add...**
3. Выберите **System Interpreter**
4. Укажите путь к Python 3.11 (например: `C:\Python311\python.exe`)
5. Нажмите **OK**

Проверить версию Python:
```bash
python --version
# Должно быть: Python 3.11.x
```
