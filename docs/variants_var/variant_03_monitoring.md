# ВАРИАНТ 03: Мониторинг и анализ производительности базы данных

---

## Задание

Разработать систему мониторинга производительности базы данных PostgreSQL с визуализацией метрик в GUI-приложении.

### Цель

Оценка умения выявлять технические проблемы, возникающие в процессе эксплуатации баз данных и серверов.

### Исходные данные

База данных PostgreSQL содержит таблицы: `users`, `notes`, `customer`, `product`, `customer_order`, `order_detail`.

Таблица `customer_order` содержит не менее 100 записей для корректного анализа.

### Требования к выполнению

#### Часть 1. Сбор метрик производительности

1. Создать модуль `db_monitor.py`:

```python
import psycopg2
from datetime import datetime, timedelta

class DatabaseMonitor:
    """Мониторинг производительности PostgreSQL"""
    
    def __init__(self, conn_params):
        self.conn_params = conn_params
    
    def get_connection(self):
        return psycopg2.connect(**self.conn_params)
    
    def get_table_sizes(self):
        """Получить размеры всех таблиц в базе данных"""
        query = """
        SELECT 
            relname AS table_name,
            pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
            pg_size_pretty(pg_relation_size(relid)) AS data_size,
            n_live_tup AS row_count
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(relid) DESC;
        """
        return self._execute_query(query)
    
    def get_slow_queries(self, threshold_ms=100):
        """Получить медленные запросы из pg_stat_statements"""
        query = """
        SELECT 
            query,
            calls,
            total_exec_time / 1000 AS total_time_sec,
            mean_exec_time / 1000 AS avg_time_sec,
            rows
        FROM pg_stat_statements
        WHERE mean_exec_time > %s
        ORDER BY mean_exec_time DESC
        LIMIT 10;
        """
        return self._execute_query(query, (threshold_ms,))
    
    def get_connection_stats(self):
        """Получить статистику подключений"""
        query = """
        SELECT 
            state,
            COUNT(*) AS count,
            SUM(total_time) AS total_time
        FROM pg_stat_activity
        GROUP BY state;
        """
        return self._execute_query(query)
    
    def get_dead_tuples(self):
        """Получить количество мёртвых кортежей (для анализа VACUUM)"""
        query = """
        SELECT 
            relname AS table_name,
            n_dead_tup AS dead_tuples,
            n_live_tup AS live_tuples,
            last_vacuum,
            last_autovacuum
        FROM pg_stat_user_tables
        ORDER BY n_dead_tup DESC;
        """
        return self._execute_query(query)
    
    def get_query_history(self, minutes=60):
        """Получить историю выполненных запросов за последние N минут"""
        query = """
        SELECT 
            query,
            query_calls,
            query_mean_time,
            query_max_time,
            query_min_time,
            query_total_time,
            query_rows
        FROM pg_stat_statements
        WHERE query_start > NOW() - INTERVAL '%s minutes'
        ORDER BY query_total_time DESC;
        """
        return self._execute_query(query, (minutes,))
    
    def _execute_query(self, query, params=None):
        """Выполнение запроса и возврат результатов"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            raise Exception(f"Ошибка выполнения запроса: {str(e)}")
```

#### Часть 2. GUI-дашборд (PyQt6)

2. Создать форму `monitor_dashboard.ui` и приложение `monitor_app.py`:

Требования к интерфейсу:
- Вкладка «Размеры таблиц» — таблица с названиями, размерами, количеством строк
- Вкладка «Медленные запросы» — список запросов с временем выполнения
- Вкладка «Подключения» — статистика активных подключений
- Вкладка «Мёртвые кортежи» — таблица для анализа необходимости VACUUM
- Кнопка «Обновить» для перезапуска сбора метрик
- Кнопка «Экспорт в CSV» для сохранения отчёта
- Цветовая индикация: зелёный — норма, жёлтый — внимание, красный — критично

#### Часть 3. Генерация отчёта

3. Создать модуль `report_generator.py`:

```python
import csv
from datetime import datetime
from db_monitor import DatabaseMonitor

class ReportGenerator:
    """Генерация отчётов по мониторингу БД"""
    
    def __init__(self, monitor: DatabaseMonitor):
        self.monitor = monitor
    
    def generate_full_report(self, filepath):
        """Создать полный отчёт в формате CSV"""
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            
            # Заголовок
            writer.writerow(["Отчёт мониторинга БД", f"Дата: {datetime.now()}"])
            writer.writerow([])
            
            # Размеры таблиц
            writer.writerow(["РАЗМЕРЫ ТАБЛИЦ"])
            writer.writerow(["Таблица", "Полный размер", "Размер данных", "Строк"])
            for row in self.monitor.get_table_sizes():
                writer.writerow([
                    row["table_name"],
                    row["total_size"],
                    row["data_size"],
                    row["row_count"]
                ])
            
            # Медленные запросы
            writer.writerow([])
            writer.writerow(["МЕДЛЕННЫЕ ЗАПРОСЫ (>100мс)"])
            writer.writerow(["Запрос", "Вызовы", "Общее время (с)", "Среднее (с)", "Строк"])
            for row in self.monitor.get_slow_queries():
                writer.writerow([
                    row["query"][:50],
                    row["calls"],
                    row["total_time_sec"],
                    row["avg_time_sec"],
                    row["rows"]
                ])
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Реализован сбор метрик (размеры таблиц, медленные запросы, подключения) | 6,00 |
| Реализован анализ мёртвых кортежей и истории запросов | 4,00 |
| Разработан GUI-дашборд с вкладками и цветовой индикацией | 7,00 |
| Реализован экспорт отчёта в CSV | 4,00 |
| Обработка исключений, комментарии, именование | 2,00 |
| Корректное подключение к PostgreSQL | 2,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- База данных PostgreSQL с таблицами из инвариантной части
- Расширение `pg_stat_statements` (опционально, для анализа медленных запросов)

### Инструкция для администратора ЦПДЭ

1. Убедиться, что PostgreSQL запущен.
2. Заполнить таблицу `customer_order` не менее 100 записями.
3. Убедиться, что `psycopg2` установлен.

### Инструкция для технического эксперта

1. Подготовить базу данных с достаточным объёмом данных.
2. При необходимости включить `pg_stat_statements`.
3. Проверить доступность метрик `pg_stat_user_tables`.
