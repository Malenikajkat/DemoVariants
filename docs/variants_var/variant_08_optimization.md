# ВАРИАНТ 08: Оптимизация SQL-запросов и индексов

---

## Задание

Разработать инструмент для анализа и оптимизации SQL-запросов PostgreSQL: создание индексов, анализ планов выполнения, выявление узких мест.

### Цель

Оценка умения выявлять технические проблемы, возникающие в процессе эксплуатации баз данных и серверов.

### Исходные данные

База данных PostgreSQL содержит таблицы из инвариантной части. Таблица `customer_order` содержит 1000+ записей, `order_detail` — 5000+ записей для корректного анализа производительности.

### Требования к выполнению

#### Часть 1. Анализатор запросов

1. Создать модуль `query_optimizer.py`:

```python
import psycopg2
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class IndexInfo:
    """Информация об индексе"""
    name: str
    table_name: str
    columns: str
    is_unique: bool
    size: str

@dataclass
class QueryPlan:
    """План выполнения запроса"""
    node_type: str
    estimated_cost: float
    estimated_rows: int
    actual_time: float
    actual_rows: int
    children: List['QueryPlan'] = None

class QueryOptimizer:
    """Анализ и оптимизация SQL-запросов"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def get_existing_indexes(self) -> List[IndexInfo]:
        """Получить список всех индексов"""
        query = """
        SELECT
            i.relname AS index_name,
            t.relname AS table_name,
            array_to_string(array_agg(a.attname), ', ') AS columns,
            ix.indisunique AS is_unique,
            pg_size_pretty(pg_relation_size(i.oid)) AS size
        FROM pg_index x
        JOIN pg_class i ON i.oid = x.indexrelid
        JOIN pg_class t ON t.oid = x.indrelid
        JOIN pg_attribute a ON a.attrelid = x.indrelid 
            AND a.attnum = ANY(x.indkey)
        WHERE t.relname LIKE 'customer%' 
           OR t.relname LIKE 'order%'
           OR t.relname = 'product'
           OR t.relname = 'specification'
        GROUP BY i.relname, t.relname, ix.indisunique, i.oid
        ORDER BY t.relname, i.relname;
        """
        return self._execute_query_indexes(query)
    
    def analyze_query_plan(self, query: str) -> Dict:
        """Анализ плана выполнения запроса (EXPLAIN ANALYZE)"""
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(explain_query)
                    plan_data = cur.fetchone()[0]
                    
                    return self._parse_plan(plan_data[0])
        except Exception as e:
            raise Exception(f"Ошибка анализа плана: {str(e)}")
    
    def find_missing_indexes(self) -> List[Dict]:
        """Поиск потенциальныхmissing индексов"""
        query = """
        SELECT
            relname AS table_name,
            seq_scan AS full_scans,
            seq_tup_read AS rows_scanned,
            idx_scan AS index_scans,
            idx_tup_fetch AS rows_fetched,
            n_live_tup AS live_rows
        FROM pg_stat_user_tables
        WHERE relname IN (
            'customer_order', 'order_detail', 'product',
            'specification', 'material', 'tech_operation'
        )
        AND seq_scan > 0
        ORDER BY 
            CASE WHEN idx_scan = 0 AND seq_scan > 10 THEN 1 ELSE 0 END,
            seq_scan DESC;
        """
        return self._execute_query(query)
    
    def suggest_indexes(self, table_name: str, where_columns: List[str]) -> List[str]:
        """
        Рекомендации по созданию индексов
        :param table_name: имя таблицы
        :param where_columns: столбцы из WHERE-условия
        :return: список SQL-команд CREATE INDEX
        """
        existing = self.get_existing_indexes()
        existing_cols = {
            idx.table_name: idx.columns.split(", ")
            for idx in existing
        }
        
        suggestions = []
        for col in where_columns:
            # Проверка, есть ли уже индекс по этому столбцу
            table_cols = existing_cols.get(table_name, [])
            if col not in table_cols:
                suggestions.append(
                    f"CREATE INDEX idx_{table_name}_{col} "
                    f"ON {table_name} ({col});"
                )
        
        return suggestions
    
    def compare_query_performance(self, query: str, iterations: int = 5) -> Dict:
        """Сравнение производительности запроса"""
        times = []
        
        for _ in range(iterations):
            query_with_timing = f"EXPLAIN (ANALYZE, FORMAT JSON) {query}"
            try:
                with psycopg2.connect(**self.db_params) as conn:
                    with conn.cursor() as cur:
                        cur.execute(query_with_timing)
                        plan = cur.fetchone()[0]
                        time_ms = plan[0]["Plan"]["Actual Total Time"]
                        times.append(time_ms)
            except Exception:
                continue
        
        if not times:
            return {"error": "Не удалось выполнить запрос"}
        
        return {
            "query": query,
            "iterations": iterations,
            "avg_time_ms": round(sum(times) / len(times), 2),
            "min_time_ms": round(min(times), 2),
            "max_time_ms": round(max(times), 2),
            "times": [round(t, 2) for t in times]
        }
    
    def _execute_query(self, query: str) -> List[Dict]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def _execute_query_indexes(self, query: str) -> List[IndexInfo]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [
                    IndexInfo(
                        name=row[0],
                        table_name=row[1],
                        columns=row[2],
                        is_unique=row[3],
                        size=row[4]
                    )
                    for row in cur.fetchall()
                ]
    
    def _parse_plan(self, plan_data: Dict) -> Dict:
        """Парсинг плана выполнения в читаемый формат"""
        def _extract(node):
            return {
                "node_type": node.get("Node Type", "Unknown"),
                "estimated_cost": node.get("Estimated Cost", 0),
                "estimated_rows": node.get("Estimated Rows", 0),
                "actual_time": node.get("Actual Total Time", 0),
                "actual_rows": node.get("Actual Rows", 0),
                "plans": [_extract(p) for p in node.get("Plans", [])]
            }
        return _extract(plan_data)
```

#### Часть 2. GUI-оптимизатор

2. Создать форму `optimizer_ui.ui` и приложение `optimizer_app.py`:

Требования к интерфейсу:
- Вкладка «Существующие индексы» — таблица с индексами
- Вкладка «Пропущенные индексы» — таблицы с полным сканированием
- Вкладка «Анализ запроса» — поле ввода SQL + результат EXPLAIN ANALYZE
- Вкладка «Рекомендации» — SQL-команды для создания индексов
- Кнопка «Сравнить производительность»
- Область визуализации плана выполнения (дерево)

#### Часть 3. Генерация отчёта об оптимизации

3. Создать модуль `optimization_report.py`:

```python
from query_optimizer import QueryOptimizer

class OptimizationReport:
    """Генерация отчёта по оптимизации"""
    
    def __init__(self, optimizer: QueryOptimizer):
        self.optimizer = optimizer
    
    def generate_report(self, filepath: str):
        """Создать текстовый отчёт"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("ОТЧЁТ ПО ОПТИМИЗАЦИИ БАЗЫ ДАННЫХ\n")
            f.write("=" * 50 + "\n\n")
            
            # Индексы
            f.write("1. СУЩЕСТВУЮЩИЕ ИНДЕКСЫ\n")
            indexes = self.optimizer.get_existing_indexes()
            for idx in indexes:
                unique = " (UNIQUE)" if idx.is_unique else ""
                f.write(f"  {idx.name} → {idx.table_name}({idx.columns}) "
                       f"[{idx.size}]{unique}\n")
            
            # Пропущенные индексы
            f.write("\n2. ПОТЕНЦИАЛЬНЫЕ ИНДЕКСЫ\n")
            missing = self.optimizer.find_missing_indexes()
            for table in missing:
                if table["index_scan"] == 0 and table["seq_scan"] > 10:
                    f.write(f"  ⚠ {table['table_name']}: "
                           f"{table['seq_scan']} полных сканирований\n")
            
            # Рекомендации
            f.write("\n3. РЕКОМЕНДАЦИИ\n")
            suggestions = self.optimizer.suggest_indexes(
                "customer_order", ["customer_id", "order_date"]
            )
            for sql in suggestions:
                f.write(f"  {sql}\n")
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Получение информации об индексах | 4,00 |
| Анализ плана выполнения (EXPLAIN ANALYZE) | 5,00 |
| Поиск пропущенных индексов | 4,00 |
| Рекомендации по созданию индексов | 4,00 |
| Сравнение производительности | 4,00 |
| GUI с вкладками и визуализацией | 3,00 |
| Обработка исключений, комментарии | 1,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- База данных PostgreSQL с таблицами из инвариантной части (1000+ записей)

### Инструкция для администратора ЦПДЭ

1. Убедиться, что PostgreSQL запущен.
2. Заполнить таблицы достаточным объёмом данных.

### Инструкция для технического эксперта

1. Подготовить базу данных с большим объёмом данных.
2. Проверить доступность системных таблиц PostgreSQL.
