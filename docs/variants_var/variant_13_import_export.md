# ВАРИАНТ 13: Разработка модуля импорта/экспорта данных

---

## Задание

Разработать универсальный модуль импорта и экспорта данных между базой данных PostgreSQL и различными форматами файлов (CSV, JSON, Excel).

### Цель

Оценка умения выполнять интеграцию модулей в программное обеспечение, организовывать заданную интеграцию на базе имеющейся архитектуры.

### Исходные данные

База данных PostgreSQL содержит таблицы: `customer`, `product`, `customer_order`, `order_detail`.

### Требования к выполнению

#### Часть 1. Модуль импорта/экспорта

1. Создать модуль `data_io.py`:

```python
import csv
import json
import io
from typing import List, Dict, Optional
from datetime import datetime
import psycopg2
import pandas as pd

class DataImporter:
    """Импорт данных из внешних файлов в БД"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def import_csv(self, filepath: str, table_name: str, 
                   delimiter: str = ",",
                   skip_header: bool = True) -> Dict:
        """Импорт данных из CSV-файла"""
        stats = {"imported": 0, "errors": 0, "skipped": 0}
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                if skip_header:
                    reader = csv.DictReader(f, delimiter=delimiter)
                else:
                    reader = csv.reader(f, delimiter=delimiter)
                
                with psycopg2.connect(**self.db_params) as conn:
                    with conn.cursor() as cur:
                        for row_num, row in enumerate(reader, 1):
                            try:
                                if skip_header:
                                    values = list(row.values())
                                    placeholders = ", ".join(["%s"] * len(values))
                                    cur.execute(
                                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                                        values
                                    )
                                else:
                                    values = list(row)
                                    placeholders = ", ".join(["%s"] * len(values))
                                    cur.execute(
                                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                                        values
                                    )
                                stats["imported"] += 1
                            except Exception as e:
                                stats["errors"] += 1
                                print(f"Ошибка строки {row_num}: {e}")
                    
                    conn.commit()
                    
        except FileNotFoundError:
            raise Exception(f"Файл не найден: {filepath}")
        except Exception as e:
            raise Exception(f"Ошибка импорта: {str(e)}")
        
        return stats
    
    def import_json(self, filepath: str, table_name: str,
                    key_mapping: Optional[Dict] = None) -> Dict:
        """Импорт данных из JSON-файла"""
        stats = {"imported": 0, "errors": 0}
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                data = [data]
            
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    for item in data:
                        try:
                            if key_mapping:
                                item = {
                                    key_mapping.get(k, k): v
                                    for k, v in item.items()
                                }
                            
                            columns = ", ".join(item.keys())
                            placeholders = ", ".join(["%s"] * len(item))
                            values = list(item.values())
                            
                            cur.execute(
                                f"INSERT INTO {table_name} ({columns}) "
                                f"VALUES ({placeholders})",
                                values
                            )
                            stats["imported"] += 1
                        except Exception as e:
                            stats["errors"] += 1
                            print(f"Ошибка записи: {e}")
                    
                    conn.commit()
        
        except Exception as e:
            raise Exception(f"Ошибка импорта JSON: {str(e)}")
        
        return stats
    
    def import_excel(self, filepath: str, table_name: str,
                     sheet_name: Optional[int] = 0) -> Dict:
        """Импорт данных из Excel-файла"""
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    inserted = 0
                    for _, row in df.iterrows():
                        try:
                            values = [
                                None if pd.isna(v) else v 
                                for v in row
                            ]
                            placeholders = ", ".join(["%s"] * len(values))
                            cur.execute(
                                f"INSERT INTO {table_name} VALUES ({placeholders})",
                                values
                            )
                            inserted += 1
                        except Exception:
                            continue
                    
                    conn.commit()
                    return {"imported": inserted}
        
        except Exception as e:
            raise Exception(f"Ошибка импорта Excel: {str(e)}")


class DataExporter:
    """Экспорт данных из БД во внешние файлы"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def export_to_csv(self, query: str, filepath: str,
                      delimiter: str = ",") -> Dict:
        """Экспорт запроса в CSV-файл"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
            
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerow(columns)
                writer.writerows(rows)
            
            return {"exported_rows": len(rows), "file": filepath}
        
        except Exception as e:
            raise Exception(f"Ошибка экспорта CSV: {str(e)}")
    
    def export_to_json(self, query: str, filepath: str) -> Dict:
        """Экспорт запроса в JSON-файл"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
            
            data = [
                dict(zip(columns, row))
                for row in rows
            ]
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return {"exported_rows": len(data), "file": filepath}
        
        except Exception as e:
            raise Exception(f"Ошибка экспорта JSON: {str(e)}")
    
    def export_to_excel(self, query: str, filepath: str,
                        sheet_name: str = "Data") -> Dict:
        """Экспорт запроса в Excel-файл"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
            
            df = pd.DataFrame(rows, columns=columns)
            df.to_excel(filepath, sheet_name=sheet_name, index=False)
            
            return {"exported_rows": len(rows), "file": filepath}
        
        except Exception as e:
            raise Exception(f"Ошибка экспорта Excel: {str(e)}")
    
    def export_table(self, table_name: str, filepath: str,
                     format: str = "csv") -> Dict:
        """Экспорт всей таблицы в указанный формат"""
        query = f"SELECT * FROM {table_name}"
        
        if format == "csv":
            return self.export_to_csv(query, filepath)
        elif format == "json":
            return self.export_to_json(query, filepath)
        elif format == "excel":
            return self.export_to_excel(query, filepath)
        else:
            raise Exception(f"Неподдерживаемый формат: {format}")
```

#### Часть 2. API-эндпоинты

2. Создать Flask-маршруты `api/io_routes.py`:

```python
from flask import Blueprint, request, jsonify, send_file
from data_io import DataImporter, DataExporter
import os

io_bp = Blueprint("io", __name__)
importer = DataImporter({"dbname": "demo_exam", "user": "postgres", "host": "localhost"})
exporter = DataExporter({"dbname": "demo_exam", "user": "postgres", "host": "localhost"})

@io_bp.route("/api/export/csv", methods=["POST"])
def export_csv():
    """Экспорт данных в CSV"""
    data = request.get_json()
    query = data.get("query")
    table = data.get("table")
    
    if not query and not table:
        return jsonify({"error": "Укажите query или table"}), 400
    
    if table:
        query = f"SELECT * FROM {table}"
    
    result = exporter.export_to_csv(query, "export.csv")
    return jsonify(result), 200

@io_bp.route("/api/import/csv", methods=["POST"])
def import_csv():
    """Импорт данных из CSV"""
    if "file" not in request.files:
        return jsonify({"error": "Файл не указан"}), 400
    
    file = request.files["file"]
    table = request.form.get("table")
    
    if not table:
        return jsonify({"error": "Имя таблицы не указано"}), 400
    
    filepath = f"temp_{file.filename}"
    file.save(filepath)
    
    result = importer.import_csv(filepath, table)
    os.remove(filepath)
    
    return jsonify(result), 200

@io_bp.route("/api/export/json", methods=["POST"])
def export_json():
    """Экспорт данных в JSON"""
    data = request.get_json()
    query = data.get("query")
    
    if not query:
        return jsonify({"error": "Запрос не указан"}), 400
    
    result = exporter.export_to_json(query, "export.json")
    return jsonify(result), 200
```

#### Часть 3. GUI-менеджер импорта/экспорта

3. Создать форму `data_io.ui` и приложение `data_io_app.py`:

Требования к интерфейсу:
- Вкладка «Импорт CSV» — выбор файла, имя таблицы, разделитель
- Вкладка «Импорт JSON» — выбор файла, имя таблицы, маппинг полей
- Вкладка «Экспорт CSV» — SQL-запрос или имя таблицы
- Вкладка «Экспорт JSON» — SQL-запрос или имя таблицы
- Вкладка «Экспорт Excel» — SQL-запрос или имя таблицы
- Кнопка «Импортировать» / «Экспортировать»
- Область результатов с подсчётом строк

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Импорт из CSV | 4,00 |
| Импорт из JSON | 4,00 |
| Импорт из Excel | 3,00 |
| Экспорт в CSV | 3,00 |
| Экспорт в JSON | 3,00 |
| Экспорт в Excel | 3,00 |
| Flask API-эндпоинты | 3,00 |
| GUI с вкладками | 2,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Библиотеки: `pandas`, `openpyxl`: `pip install pandas openpyxl`
- Тестовые файлы: test.csv, test.json

### Инструкция для администратора ЦПДЭ

1. Убедиться, что `pandas` и `openpyxl` установлены.
2. Подготовить тестовые файлы для импорта.

### Инструкция для технического эксперта

1. Установить `pandas` и `openpyxl`.
2. Подготовить тестовые CSV и JSON файлы.
