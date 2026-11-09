# ВАРИАНТ 18: Разработка модуля поиска и фильтрации данных

---

## Задание

Разработать универсальный модуль поиска и фильтрации данных с поддержкой полнотекстового поиска, сложных условий и пагинации.

### Цель

Оценка умения производить разработку модулей информационной системы в соответствии с техническим заданием.

### Исходные данные

Таблицы: `customer`, `product`, `customer_order`, `order_detail`.

### Требования к выполнению

#### Часть 1. Модуль поиска и фильтрации

1. Создать модуль `search_engine.py`:

```python
import psycopg2
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class FilterCondition:
    """Условие фильтрации"""
    column: str
    operator: str       # =, !=, >, <, >=, <=, LIKE, IN, BETWEEN
    value: Any

@dataclass
class SearchRequest:
    """Запрос на поиск"""
    table: str
    search_term: Optional[str] = None
    filters: List[FilterCondition] = field(default_factory=list)
    sort_column: Optional[str] = None
    sort_order: str = "ASC"  # ASC, DESC
    page: int = 1
    page_size: int = 20

@dataclass
class SearchResults:
    """Результаты поиска"""
    rows: List[Dict]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    search_time_ms: float

class SearchEngine:
    """Универсальный поисковый движок"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def search(self, request: SearchRequest) -> SearchResults:
        """Выполнение поиска с фильтрацией и пагинацией"""
        import time
        start_time = time.time()
        
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    # Подсчёт общего количества
                    count_query = self._build_count_query(request)
                    cur.execute(count_query, self._get_filter_params(request))
                    total_count = cur.fetchone()[0]
                    
                    # Получение данных
                    data_query = self._build_data_query(request)
                    cur.execute(data_query, self._get_all_params(request))
                    rows = cur.fetchall()
                    
                    # Получение имён столбцов
                    columns = [desc[0] for desc in cur.description]
                    result_rows = [dict(zip(columns, row)) for row in rows]
            
            elapsed_ms = (time.time() - start_time) * 1000
            total_pages = (total_count + request.page_size - 1) // request.page_size
            
            return SearchResults(
                rows=result_rows,
                total_count=total_count,
                page=request.page,
                page_size=request.page_size,
                total_pages=total_pages,
                search_time_ms=round(elapsed_ms, 2)
            )
        
        except Exception as e:
            raise Exception(f"Ошибка поиска: {str(e)}")
    
    def fulltext_search(self, table: str, columns: List[str],
                         search_term: str, limit: int = 50) -> List[Dict]:
        """Полнотекстовый поиск по нескольким столбцам"""
        search_word = search_term.replace(" ", " & ")
        
        conditions = " OR ".join(
            f"to_tsvector('russian', {col}) @@ plainto_tsquery('russian', %s)"
            for col in columns
        )
        
        query = f"""
        SELECT * FROM {table}
        WHERE {conditions}
        ORDER BY 
            CASE WHEN {columns[0]} ILIKE %s THEN 0 ELSE 1 END,
            {columns[0]}
        LIMIT %s;
        """
        
        params = [search_word, f"%{search_term}%", limit]
        return self._execute_query(query, tuple(params))
    
    def advanced_filter(self, table: str, conditions: List[Dict],
                         sort_column: str = None, sort_order: str = "ASC",
                         limit: int = 100) -> List[Dict]:
        """Сложная фильтрация с динамическими условиями"""
        where_clauses = []
        params = []
        
        for cond in conditions:
            col = cond.get("column")
            op = cond.get("operator", "=")
            value = cond.get("value")
            
            if op == "IN":
                placeholders = ", ".join(["%s"] * len(value))
                where_clauses.append(f"{col} IN ({placeholders})")
                params.extend(value)
            elif op == "BETWEEN":
                where_clauses.append(f"{col} BETWEEN %s AND %s")
                params.extend(value)
            elif op == "IS_NULL":
                where_clauses.append(f"{col} IS {'NOT ' if not value else ''}NULL")
            elif op == "LIKE":
                where_clauses.append(f"{col} LIKE %s")
                params.append(f"%{value}%")
            else:
                where_clauses.append(f"{col} {op} %s")
                params.append(value)
        
        query = f"SELECT * FROM {table}"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        if sort_column:
            query += f" ORDER BY {sort_column} {sort_order}"
        
        query += f" LIMIT {limit}"
        
        return self._execute_query(query, tuple(params))
    
    def get_search_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """История поисковых запросов"""
        query = """
        SELECT search_term, table_name, created_at, result_count
        FROM search_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """
        return self._execute_query(query, (user_id, limit))
    
    def _build_count_query(self, request: SearchRequest) -> str:
        base = f"SELECT COUNT(*) FROM {request.table}"
        where, _ = self._build_where_clause(request)
        if where:
            base += " WHERE " + where
        return base
    
    def _build_data_query(self, request: SearchRequest) -> str:
        base = f"SELECT * FROM {request.table}"
        where, _ = self._build_where_clause(request)
        if where:
            base += " WHERE " + where
        
        if request.sort_column:
            base += f" ORDER BY {request.sort_column} {request.sort_order}"
        
        base += f" LIMIT {request.page_size} OFFSET {((request.page - 1) * request.page_size)}"
        return base
    
    def _build_where_clause(self, request: SearchRequest) -> Tuple[str, List]:
        clauses = []
        params = []
        
        if request.search_term:
            clauses.append(
                f"({request.table}.*::text ILIKE %s)"
            )
            params.append(f"%{request.search_term}%")
        
        for f in request.filters:
            if f.operator == "LIKE":
                clauses.append(f"{f.column} LIKE %s")
                params.append(f"%{f.value}%")
            elif f.operator == "IN":
                placeholders = ", ".join(["%s"] * len(f.value))
                clauses.append(f"{f.column} IN ({placeholders})")
                params.extend(f.value)
            elif f.operator == "BETWEEN":
                clauses.append(f"{f.column} BETWEEN %s AND %s")
                params.extend(f.value)
            else:
                clauses.append(f"{f.column} {f.operator} %s")
                params.append(f.value)
        
        return " AND ".join(clauses), params
    
    def _get_filter_params(self, request: SearchRequest) -> list:
        _, params = self._build_where_clause(request)
        return params
    
    def _get_all_params(self, request: SearchRequest) -> list:
        params = self._get_filter_params(request)
        params.append(request.page_size)
        params.append((request.page - 1) * request.page_size)
        return params
    
    def _execute_query(self, query: str, params=None) -> List[Dict]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
```

#### Часть 2. GUI-панель поиска

2. Создать форму `search_panel.ui` и приложение `search_app.py`:

Требования к интерфейсу:
- Поле быстрого поиска (полнотекстовый)
- Выбор таблицы для поиска (customer, product, customer_order)
- Динамические фильтры (добавление/удаление условий)
- Таблица результатов с пагинацией
- Кнопки «Назад» / «Вперёд»
- Счётчик результатов и время поиска
- История поиска
- Сортировка по столбцам (клик по заголовку)

#### Часть 3. API-эндпоинты поиска

3. Создать Flask-маршруты `api/search_routes.py`:

```python
from flask import Blueprint, request, jsonify
from search_engine import SearchEngine, SearchRequest, FilterCondition

search_bp = Blueprint("search", __name__)
engine = SearchEngine({"dbname": "demo_exam", "user": "postgres", "host": "localhost"})

@search_bp.route("/api/search", methods=["GET"])
def search():
    """Универсальный поиск"""
    table = request.args.get("table", "customer")
    term = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    
    request_obj = SearchRequest(
        table=table,
        search_term=term,
        page=page,
        page_size=page_size
    )
    
    results = engine.search(request_obj)
    
    return jsonify({
        "rows": results.rows,
        "total": results.total_count,
        "page": results.page,
        "page_size": results.page_size,
        "total_pages": results.total_pages,
        "search_time_ms": results.search_time_ms
    }), 200

@search_bp.route("/api/search/fulltext", methods=["GET"])
def fulltext_search():
    """Полнотекстовый поиск"""
    term = request.args.get("q", "")
    table = request.args.get("table", "customer")
    columns = request.args.get("columns", "name").split(",")
    
    results = engine.fulltext_search(table, columns, term)
    return jsonify({"results": results}), 200
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Универсальный поиск с пагинацией | 5,00 |
| Полнотекстовый поиск (russian) | 4,00 |
| Сложная фильтрация (IN, BETWEEN, LIKE) | 4,00 |
| Сортировка и пагинация | 4,00 |
| История поиска | 3,00 |
| Flask API-эндпоинты | 3,00 |
| GUI-панель поиска | 2,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Таблицы из инвариантной части с данными
- Таблица `search_history` (опционально)

### Инструкция для администратора ЦПДЭ

1. Убедиться, что PostgreSQL запущен и заполнен данными.
2. Проверить наличие psycopg2.

### Инструкция для технического эксперта

1. Подготовить базу данных.
2. Проверить поддержку полнотекстового поиска PostgreSQL.
