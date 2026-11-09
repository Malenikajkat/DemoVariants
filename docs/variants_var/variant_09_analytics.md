# ВАРИАНТ 09: Разработка отчётов и аналитики на основе данных ИС

---

## Задание

Разработать модуль генерации аналитических отчётов на основе данных информационной системы с визуализацией в GUI-приложении.

### Цель

Оценка умения использовать современные средства поиска, анализа и интерпретации информации и информационные технологии для выполнения задач профессиональной деятельности.

### Исходные данные

База данных PostgreSQL содержит таблицы: `customer_order`, `order_detail`, `product`, `material`, `customer`, `users`.

### Требования к выполнению

#### Часть 1. Модуль аналитики

1. Создать модуль `analytics_engine.py`:

```python
import psycopg2
from typing import List, Dict
from datetime import datetime, timedelta

class AnalyticsEngine:
    """Аналитический движок для ИС"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def get_sales_by_product(self) -> List[Dict]:
        """Выручка по продуктам"""
        query = """
        SELECT 
            p.name AS product_name,
            SUM(od.quantity) AS total_quantity,
            SUM(od.quantity * od.price) AS total_revenue,
            COUNT(DISTINCT co.id) AS order_count
        FROM order_detail od
        JOIN product p ON od.product_id = p.id
        JOIN customer_order co ON od.order_id = co.id
        GROUP BY p.name
        ORDER BY total_revenue DESC;
        """
        return self._execute(query)
    
    def get_sales_by_period(self, days: int = 30) -> List[Dict]:
        """Продажи по дням за последние N дней"""
        query = """
        SELECT 
            DATE(co.order_date) AS sale_date,
            COUNT(*) AS order_count,
            SUM(od.quantity * od.price) AS daily_revenue
        FROM customer_order co
        JOIN order_detail od ON co.id = od.order_id
        WHERE co.order_date >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(co.order_date)
        ORDER BY sale_date;
        """
        return self._execute(query, (days,))
    
    def get_top_customers(self, limit: int = 10) -> List[Dict]:
        """Топ-клиенты по сумме заказов"""
        query = """
        SELECT 
            c.name AS customer_name,
            c.type AS customer_type,
            COUNT(co.id) AS order_count,
            SUM(od.quantity * od.price) AS total_spent
        FROM customer c
        JOIN customer_order co ON c.id = co.customer_id
        JOIN order_detail od ON co.id = od.order_id
        GROUP BY c.id, c.name, c.type
        ORDER BY total_spent DESC
        LIMIT %s;
        """
        return self._execute(query, (limit,))
    
    def get_material_consumption(self) -> List[Dict]:
        """Расход материалов по продуктам"""
        query = """
        SELECT 
            m.name AS material_name,
            s.quantity_per_unit AS quantity_per_product,
            p.name AS product_name,
            s.quantity_per_unit * SUM(od.quantity) AS total_consumed,
            m.unit AS unit
        FROM specification s
        JOIN material m ON s.material_id = m.id
        JOIN product p ON s.product_id = p.id
        JOIN order_detail od ON p.id = od.product_id
        GROUP BY m.id, m.name, s.quantity_per_unit, p.name, m.unit
        ORDER BY total_consumed DESC;
        """
        return self._execute(query)
    
    def get_order_status_summary(self) -> List[Dict]:
        """Статистика по статусам заказов"""
        query = """
        SELECT 
            status,
            COUNT(*) AS count,
            ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 1) AS percentage
        FROM customer_order
        GROUP BY status
        ORDER BY count DESC;
        """
        return self._execute(query)
    
    def get_average_order_value(self) -> Dict:
        """Средний чек и статистика заказов (вычисляется через JOIN)"""
        query = """
        SELECT 
            COUNT(DISTINCT co.id) AS total_orders,
            ROUND(COALESCE(AVG(line_total), 0), 2) AS avg_order_value,
            ROUND(COALESCE(MIN(line_total), 0), 2) AS min_order_value,
            ROUND(COALESCE(MAX(line_total), 0), 2) AS max_order_value,
            ROUND(COALESCE(SUM(line_total), 0), 2) AS total_revenue
        FROM (
            SELECT co.id, SUM(od.quantity * od.price) AS line_total
            FROM customer_order co
            LEFT JOIN order_detail od ON co.id = od.order_id
            GROUP BY co.id
        ) line_totals;
        """
        return self._execute(query)[0] if self._execute(query) else {}
    
    def get_department_performance(self) -> List[Dict]:
        """Эффективность подразделений/исполнителей"""
        query = """
        SELECT 
            executor,
            COUNT(*) AS order_count,
            ROUND(AVG(order_total), 2) AS avg_value,
            ROUND(SUM(order_total), 2) AS total_value
        FROM customer_order
        GROUP BY executor
        ORDER BY total_value DESC;
        """
        return self._execute(query)
    
    def _execute(self, query: str, params=None) -> List[Dict]:
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception as e:
            raise Exception(f"Ошибка выполнения запроса: {str(e)}")
```

#### Часть 2. GUI-дашборд отчётов

2. Создать форму `report_dashboard.ui` и приложение `report_app.py`:

Требования к интерфейсу:
- Вкладка «Выручка по продуктам» — таблица + столбчатая диаграмма
- Вкладка «Продажи по дням» — линейный график
- Вкладка «Топ-клиенты» — таблица с рейтингом
- Вкладка «Расход материалов» — таблица
- Вкладка «Статусы заказов» — круговая диаграмма
- Вкладка «Средний чек» — карточки со статистикой
- Кнопка «Экспорт отчёта» — сохранение в CSV
- Выбор периода (дата начала — дата окончания)

#### Часть 3. Экспорт отчётов

3. Создать модуль `report_exporter.py`:

```python
import csv
from analytics_engine import AnalyticsEngine

class ReportExporter:
    """Экспорт аналитических отчётов"""
    
    def __init__(self, engine: AnalyticsEngine):
        self.engine = engine
    
    def export_sales_to_csv(self, filepath: str):
        """Экспорт продаж по продуктам в CSV"""
        data = self.engine.get_sales_by_product()
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    def export_summary_to_csv(self, filepath: str):
        """Экспорт сводного отчёта"""
        avg = self.engine.get_average_order_value()
        status = self.engine.get_order_status_summary()
        
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["СВОДНЫЙ ОТЧЁТ"])
            writer.writerow([])
            writer.writerow(["Показатель", "Значение"])
            writer.writerow(["Всего заказов", avg.get("total_orders", 0)])
            writer.writerow(["Средний чек", avg.get("avg_order_value", 0)])
            writer.writerow(["Мин. заказ", avg.get("min_order_value", 0)])
            writer.writerow(["Макс. заказ", avg.get("max_order_value", 0)])
            writer.writerow(["Общая выручка", avg.get("total_revenue", 0)])
            writer.writerow([])
            writer.writerow(["Статусы заказов"])
            writer.writerow(["Статус", "Кол-во", "%"])
            for s in status:
                writer.writerow([s["status"], s["count"], s["percentage"]])
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Аналитические SQL-запросы (7 метрик) | 6,00 |
| Выручка по продуктам и периодам | 4,00 |
| Топ-клиенты и статусы заказов | 4,00 |
| GUI-дашборд с вкладками | 5,00 |
| Экспорт в CSV | 3,00 |
| Выбор периода и фильтрация | 2,00 |
| Обработка исключений, комментарии | 1,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- База данных PostgreSQL с заполненными таблицами

### Инструкция для администратора ЦПДЭ

1. Убедиться, что PostgreSQL запущен и заполнен данными.
2. Проверить наличие psycopg2.

### Инструкция для технического эксперта

1. Подготовить базу данных с данными для аналитики.
2. Проверить работоспособность psycopg2.
