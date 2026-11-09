# ВАРИАНТ 04: Разработка пользовательской документации и инструкций

---

## Задание

Разработать модуль генерации пользовательской документации для информационной системы в формате PDF с использованием Python.

### Цель

Оценка умения разрабатывать проектную документацию на информационную систему в соответствии с требованиями заказчика.

### Исходные данные

Информационная система включает следующие модули:
- Модуль авторизации (форма входа с капчей)
- Панель администратора (управление пользователями)
- API-эндпоинты (GET /notes, GET /api/notes)

### Требования к выполнению

#### Часть 1. Модуль сбора данных для документации

1. Создать модуль `doc_collector.py`:

```python
import psycopg2
import inspect
from typing import Dict, List, Any

class DocumentationCollector:
    """Сбор данных для генерации документации ИС"""
    
    def __init__(self, db_params: Dict):
        self.db_params = db_params
    
    def get_database_schema(self) -> List[Dict]:
        """Получить схему базы данных (таблицы, столбцы, ключи)"""
        query = """
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.is_nullable,
            pk.constraint_type AS is_primary_key,
            fk.constraint_type AS is_foreign_key,
            fk.referenced_table_name
        FROM information_schema.columns c
        JOIN information_schema.tables t 
            ON c.table_name = t.table_name 
            AND t.table_schema = 'public'
        LEFT JOIN (
            SELECT 
                kcu.table_name,
                kcu.column_name,
                'PRIMARY KEY' AS constraint_type
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
        ) pk ON c.table_name = pk.table_name AND c.column_name = pk.column_name
        LEFT JOIN (
            SELECT 
                kcu.table_name,
                kcu.column_name,
                'FOREIGN KEY' AS constraint_type,
                kcu.referenced_table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.referential_constraints rc
                ON tc.constraint_name = rc.constraint_name
                AND tc.table_schema = rc.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
        ) fk ON c.table_name = fk.table_name AND c.column_name = fk.column_name
        WHERE t.table_type = 'BASE TABLE'
        ORDER BY t.table_name, c.ordinal_position;
        """
        return self._execute_query(query)
    
    def get_api_endpoints(self) -> List[Dict]:
        """Получить список API-эндпоинтов (анализ Flask-маршрутов)"""
        from flask import Flask
        app = Flask(__name__)
        
        endpoints = []
        for rule in app.url_map.iter_rules():
            endpoints.append({
                "path": str(rule),
                "methods": list(rule.methods),
                "description": self._get_endpoint_description(rule)
            })
        return endpoints
    
    def get_user_roles(self) -> List[Dict]:
        """Получить список ролей пользователей из БД"""
        query = """
        SELECT DISTINCT role 
        FROM users 
        WHERE role IS NOT NULL
        ORDER BY role;
        """
        result = self._execute_query(query)
        return [{"role": row["role"]} for row in result]
    
    def _execute_query(self, query: str, params=None) -> List[Dict]:
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception as e:
            raise Exception(f"Ошибка: {str(e)}")
    
    def _get_endpoint_description(self, rule) -> str:
        """Получение описания эндпоинта"""
        descriptions = {
            "/notes": "Получение списка заметок",
            "/api/notes": "API: получение списка заметок",
            "/login": "Авторизация пользователя",
            "/users": "Управление пользователями"
        }
        return descriptions.get(str(rule), "Описание не задано")
```

#### Часть 2. Генерация документации в PDF

2. Создать модуль `pdf_generator.py` с использованием библиотеки `reportlab`:

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, 
    TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from doc_collector import DocumentationCollector

class PDFGenerator:
    """Генерация документации в формате PDF"""
    
    def __init__(self, collector: DocumentationCollector):
        self.collector = collector
    
    def generate_full_documentation(self, output_path: str):
        """Создать полную документацию ИС"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Титульная страница
        story.append(Paragraph("Документация информационной системы", 
                               styles["Title"]))
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Специалист по информационным системам", 
                               styles["Normal"]))
        story.append(Spacer(1, 2*cm))
        
        # Оглавление
        story.append(Paragraph("Оглавление", styles["Heading1"]))
        story.append(Paragraph("1. Описание системы", styles["Heading2"]))
        story.append(Paragraph("2. Схема базы данных", styles["Heading2"]))
        story.append(Paragraph("3. API-документация", styles["Heading2"]))
        story.append(Paragraph("4. Ролевая модель", styles["Heading2"]))
        story.append(Paragraph("5. Инструкции по использованию", styles["Heading2"]))
        story.append(PageBreak())
        
        # 1. Описание системы
        story.append(Paragraph("1. Описание системы", styles["Heading1"]))
        story.append(Paragraph(
            "Информационная система предназначена для управления "
            "производством и продажами предприятия. Система включает "
            "десктопное приложение на PyQt6 и REST API на Flask.",
            styles["Normal"]
        ))
        
        # 2. Схема базы данных
        story.append(Paragraph("2. Схема базы данных", styles["Heading1"]))
        schema = self.collector.get_database_schema()
        tables = self._group_by_table(schema)
        
        for table_name, columns in tables.items():
            story.append(Paragraph(f"Таблица: {table_name}", styles["Heading2"]))
            data = [["Поле", "Тип", "Длина", "Nullable", "Ключ"]]
            for col in columns:
                key_info = ""
                if col.get("is_primary_key"):
                    key_info = "PK"
                elif col.get("is_foreign_key"):
                    key_info = f"FK → {col['referenced_table_name']}"
                data.append([
                    col["column_name"],
                    col["data_type"],
                    str(col.get("character_maximum_length", "-")),
                    "Да" if col["is_nullable"] == "YES" else "Нет",
                    key_info
                ])
            
            t = Table(data, colWidths=[3*cm, 3*cm, 2*cm, 2*cm, 3*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5*cm))
        
        # 3. API-документация
        story.append(Paragraph("3. API-документация", styles["Heading1"]))
        endpoints = self.collector.get_api_endpoints()
        for ep in endpoints:
            story.append(Paragraph(
                f"Метод: {', '.join(ep['methods'])} | Путь: {ep['path']}",
                styles["Heading3"]
            ))
            story.append(Paragraph(ep["description"], styles["Normal"]))
        
        # 4. Ролевая модель
        story.append(Paragraph("4. Ролевая модель", styles["Heading1"]))
        roles = self.collector.get_user_roles()
        for role in roles:
            story.append(Paragraph(f"• {role['role']}", styles["Normal"]))
        
        doc.build(story)
    
    def _group_by_table(self, schema: List[Dict]) -> Dict:
        tables = {}
        for col in schema:
            table = col["table_name"]
            if table not in tables:
                tables[table] = []
            tables[table].append(col)
        return tables
```

#### Часть 3. GUI-приложение для генерации

3. Создать форму `doc_generator.ui` и приложение `doc_app.py`:

Требования к интерфейсу:
- Поля подключения к БД
- Чекбоксы разделов: «Схема БД», «API-документация», «Ролевая модель»
- Поле для указания пути сохранения PDF
- Кнопка «Сгенерировать»
- Прогресс-бар и область логов

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Реализован сбор схемы БД (таблицы, столбцы, ключи) | 5,00 |
| Реализован сбор API-эндпоинтов | 4,00 |
| Реализована генерация PDF с таблицами и стилями | 7,00 |
| Разработан GUI для управления генерацией | 5,00 |
| Документ содержит все обязательные разделы | 3,00 |
| Обработка исключений, комментарии, именование | 1,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Библиотека `reportlab`: `pip install reportlab`
- База данных PostgreSQL с таблицами из инвариантной части

### Инструкция для администратора ЦПДЭ

1. Убедиться, что `reportlab` установлен.
2. Подготовить базу данных с таблицами.

### Инструкция для технического эксперта

1. Установить `reportlab` на всех рабочих местах.
2. Подготовить базу данных.
