# ВАРИАНТ 16: Создание дашборда визуализации данных

---

## Задание

Разработать GUI-дашборд с визуализацией ключевых метрик информационной системы с использованием графиков и диаграмм.

### Цель

Оценка умения использовать современные средства поиска, анализа и интерпретации информации и информационные технологии для выполнения задач профессиональной деятельности.

### Исходные данные

База данных PostgreSQL содержит таблицы: `customer_order`, `order_detail`, `product`, `customer`.

### Требования к выполнению

#### Часть 1. Модуль сбора метрик для дашборда

1. Создать модуль `dashboard_metrics.py`:

```python
import psycopg2
from typing import Dict, List
from datetime import datetime, timedelta

class DashboardMetrics:
    """Сбор метрик для дашборда"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def get_kpi_cards(self) -> Dict:
        """Ключевые показатели (карточки KPI)"""
        metrics = {}
        
        # Общее количество заказов
        metrics["total_orders"] = self._scalar_query(
            "SELECT COUNT(*) FROM customer_order"
        )
        
        # Общая выручка (вычисляется через JOIN с order_detail)
        metrics["total_revenue"] = self._scalar_query(
            "SELECT COALESCE(SUM(od.quantity * od.price), 0) "
            "FROM order_detail od"
        )
        
        # Средний чек
        metrics["avg_order"] = self._scalar_query(
            "SELECT COALESCE(ROUND(SUM(od.quantity * od.price) / COUNT(DISTINCT co.id), 2), 0) "
            "FROM customer_order co "
            "JOIN order_detail od ON co.id = od.order_id"
        )
        
        # Активные заказы
        metrics["active_orders"] = self._scalar_query(
            "SELECT COUNT(*) FROM customer_order WHERE status = 'В работе'"
        )
        
        # Количество клиентов
        metrics["total_customers"] = self._scalar_query(
            "SELECT COUNT(*) FROM customer"
        )
        
        # Количество продуктов
        metrics["total_products"] = self._scalar_query(
            "SELECT COUNT(*) FROM product"
        )
        
        return metrics
    
    def get_orders_trend(self, days: int = 30) -> List[Dict]:
        """Динамика заказов по дням (для линейного графика)"""
        query = """
        SELECT 
            DATE(co.order_date) AS date,
            COUNT(DISTINCT co.id) AS order_count,
            COALESCE(SUM(od.quantity * od.price), 0) AS revenue
        FROM customer_order co
        LEFT JOIN order_detail od ON co.id = od.order_id
        WHERE co.order_date >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(co.order_date)
        ORDER BY date;
        """
        return self._execute_query(query, (days,))
    
    def get_sales_by_product(self, limit: int = 10) -> List[Dict]:
        """Продажи по продуктам (для столбчатой диаграммы)"""
        query = """
        SELECT 
            p.name AS product_name,
            SUM(od.quantity) AS total_quantity,
            SUM(od.quantity * od.price) AS total_revenue
        FROM order_detail od
        JOIN product p ON od.product_id = p.id
        GROUP BY p.name
        ORDER BY total_revenue DESC
        LIMIT %s;
        """
        return self._execute_query(query, (limit,))
    
    def get_order_status_distribution(self) -> List[Dict]:
        """Распределение заказов по статусам (для круговой диаграммы)"""
        query = """
        SELECT 
            status,
            COUNT(*) AS count,
            ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 1) AS percentage
        FROM customer_order
        GROUP BY status
        ORDER BY count DESC;
        """
        return self._execute_query(query)
    
    def get_customers_by_type(self) -> List[Dict]:
        """Клиенты по типу (для круговой диаграммы)"""
        query = """
        SELECT 
            customer_type AS type,
            COUNT(*) AS count
        FROM customer
        GROUP BY customer_type
        ORDER BY count DESC;
        """
        return self._execute_query(query)
    
    def get_top_customers_revenue(self, limit: int = 8) -> List[Dict]:
        """Топ-клиенты по выручке (для горизонтальной диаграммы)"""
        query = """
        SELECT 
            c.name AS customer_name,
            SUM(od.quantity * od.price) AS total_revenue
        FROM customer c
        JOIN customer_order co ON c.id = co.customer_id
        JOIN order_detail od ON co.id = od.order_id
        GROUP BY c.name
        ORDER BY total_revenue DESC
        LIMIT %s;
        """
        return self._execute_query(query, (limit,))
    
    def get_daily_revenue(self, days: int = 14) -> List[Dict]:
        """Выручка по дням (для area chart)"""
        query = """
        SELECT 
            DATE(co.order_date) AS date,
            COALESCE(SUM(od.quantity * od.price), 0) AS revenue
        FROM customer_order co
        LEFT JOIN order_detail od ON co.id = od.order_id
        WHERE co.order_date >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(co.order_date)
        ORDER BY date;
        """
        return self._execute_query(query, (days,))
    
    def _scalar_query(self, query: str, params=None):
        """Выполнение запроса с возвратом одного значения"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    result = cur.fetchone()[0]
                    return result if result else 0
        except Exception:
            return 0
    
    def _execute_query(self, query: str, params=None) -> List[Dict]:
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception as e:
            raise Exception(f"Ошибка: {str(e)}")
```

#### Часть 2. GUI-дашборд с графиками

2. Создать форму `dashboard.ui` и приложение `dashboard_app.py`:

Требования к интерфейсу:
- Верхняя панель: 6 карточек KPI (заказы, выручка, средний чек, активные, клиенты, продукты)
- График 1: Динамика заказов (линейный, pyqtgraph >= 0.13.0)
- График 2: Продажи по продуктам (столбчатый)
- График 3: Распределение по статусам (круговой)
- График 4: Топ-клиенты (горизонтальный)
- График 5: Выручка по дням (area chart)
- Кнопка «Обновить данные»
- Выбор периода (сегодня / неделя / месяц / квартал)
- Автоматическое обновление каждые 30 секунд

#### Часть 3. Интеграция с pyqtgraph (PyQt6)

3. Создать модуль `chart_renderer.py`:

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg  # requires pyqtgraph >= 0.13.0 for PyQt6 support

class ChartRenderer:
    """Рендеринг графиков на PyQt"""
    
    @staticmethod
    def create_line_chart(data: List[Dict], x_key: str, y_key: str,
                           title: str = "") -> pg.PlotWidget:
        """Создание линейного графика"""
        plot_widget = pg.PlotWidget(title=title)
        
        x_values = [item[x_key] for item in data]
        y_values = [item[y_key] for item in data]
        
        plot_widget.plot(x_values, y_values, pen="b", symbol="o", symbolSize=6)
        plot_widget.setLabel("left", "Значение")
        plot_widget.setLabel("bottom", "Период")
        
        return plot_widget
    
    @staticmethod
    def create_bar_chart(data: List[Dict], x_key: str, y_key: str,
                         title: str = "") -> pg.PlotWidget:
        """Создание столбчатой диаграммы"""
        plot_widget = pg.PlotWidget(title=title)
        
        x_values = list(range(len(data)))
        y_values = [item[y_key] for item in data]
        labels = [item[x_key] for item in data]
        
        bar_chart = pg.BarGraphItem(
            x=x_values, height=y_values, width=0.6,
            brushes=["#3498db"]
        )
        plot_widget.addItem(bar_chart)
        
        return plot_widget
    
    @staticmethod
    def create_pie_chart(data: List[Dict], label_key: str, 
                         value_key: str, title: str = "") -> pg.PlotWidget:
        """Создание круговой диаграммы"""
        plot_widget = pg.PlotWidget(title=title)
        
        values = [item[value_key] for item in data]
        labels = [item[label_key] for item in data]
        
        pie_chart = pg.PieItem(
            values=values, 
            labels=labels,
            brushes=["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]
        )
        plot_widget.addItem(pie_chart)
        
        return plot_widget
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Сбор метрик KPI (6 карточек) | 4,00 |
| Линейный график динамики заказов | 4,00 |
| Столбчатая диаграмма продаж | 4,00 |
| Круговая диаграмма статусов | 3,00 |
| Горизонтальная диаграмма топ-клиентов | 3,00 |
| Area chart выручки | 3,00 |
| GUI-дашборд с автообновлением | 4,00 |
| Обработка исключений, комментарии | 0,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Библиотека `pyqtgraph >= 0.13.0` (поддержка PyQt6): `pip install pyqtgraph>=0.13.0`
- База данных PostgreSQL с заполненными таблицами

### Инструкция для администратора ЦПДЭ

1. Убедиться, что `pyqtgraph>=0.13.0` установлен (`pip install pyqtgraph>=0.13.0`).
2. Подготовить базу данных с данными.

### Инструкция для технического эксперта

1. Установить `pyqtgraph>=0.13.0` на всех рабочих местах.
2. Проверить работоспособность PostgreSQL.
