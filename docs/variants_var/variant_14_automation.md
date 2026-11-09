# ВАРИАНТ 14: Автоматизация бизнес-процессов (триггеры, хранимые процедуры)

---

## Задание

Разработать набор триггеров и хранимых процедур PostgreSQL для автоматизации бизнес-процессов: расчёт стоимости заказа, обновление остатков, генерация отчётов.

### Цель

Оценка умения осуществлять администрирование отдельных компонент серверов и выполнять интеграцию модулей.

### Исходные данные

Таблицы: `customer_order`, `order_detail`, `product`, `specification`, `material`, `tech_operation`.

### Требования к выполнению

#### Часть 1. Хранимые процедуры и функции

1. Создать SQL-файл `procedures/business_logic.sql`:

```sql
-- =============================================
-- Хранимая процедура: расчёт стоимости заказа
-- =============================================
CREATE OR REPLACE FUNCTION calculate_order_total(p_order_id INTEGER)
RETURNS TABLE (
    order_id INTEGER,
    product_name VARCHAR,
    quantity INTEGER,
    material_cost DECIMAL,
    operation_cost DECIMAL,
    line_total DECIMAL,
    order_total DECIMAL
) AS $$
DECLARE
    v_material_cost DECIMAL := 0;
    v_operation_cost DECIMAL := 0;
    v_order_total DECIMAL := 0;
    v_product RECORD;
BEGIN
    FOR v_product IN
        SELECT od.product_id, od.quantity, od.price
        FROM order_detail od
        WHERE od.order_id = p_order_id
    LOOP
        -- Расчёт стоимости материалов
        SELECT COALESCE(SUM(s.quantity_per_unit * m.price), 0)
        INTO v_material_cost
        FROM specification s
        JOIN material m ON s.material_id = m.id
        WHERE s.product_id = v_product.product_id;
        
        -- Расчёт стоимости операций
        SELECT COALESCE(SUM(s.time_norm * to.price), 0)
        INTO v_operation_cost
        FROM specification s
        JOIN tech_operation to ON s.operation_id = to.id
        WHERE s.product_id = v_product.product_id;
        
        v_line_total := v_product.quantity * (v_material_cost + v_operation_cost);
        v_order_total := v_order_total + v_line_total;
        
        RETURN QUERY
        SELECT
            p_order_id,
            p.name,
            v_product.quantity,
            v_material_cost,
            v_operation_cost,
            v_line_total,
            v_order_total
        FROM product p
        WHERE p.id = v_product.product_id;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Триггер: автоматическое обновление order_total
-- =============================================
CREATE OR REPLACE FUNCTION update_order_total_trigger()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customer_order
    SET order_total = (
        SELECT COALESCE(SUM(quantity * price), 0)
        FROM order_detail
        WHERE order_id = NEW.order_id
    )
    WHERE id = NEW.order_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_order_total
    AFTER INSERT OR UPDATE OR DELETE ON order_detail
    FOR EACH ROW
    EXECUTE FUNCTION update_order_total_trigger();

-- =============================================
-- Хранимая процедура: создание заказа
-- =============================================
CREATE OR REPLACE FUNCTION create_customer_order(
    p_customer_id INTEGER,
    p_products INTEGER[],
    p_quantities INTEGER[]
)
RETURNS INTEGER AS $$
DECLARE
    v_order_id INTEGER;
    v_i INTEGER;
BEGIN
    -- Создание заказа
    INSERT INTO customer_order (customer_id, order_date, status)
    VALUES (p_customer_id, NOW(), 'Новый')
    RETURNING id INTO v_order_id;
    
    -- Добавление позиций
    FOR v_i IN 1..array_length(p_products, 1) LOOP
        INSERT INTO order_detail (order_id, product_id, quantity, price)
        VALUES (
            v_order_id,
            p_products[v_i],
            p_quantities[v_i],
            (SELECT price FROM product WHERE id = p_products[v_i])
        );
    END LOOP;
    
    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Хранимая процедура: генерация ежемесячного отчёта
-- =============================================
CREATE OR REPLACE PROCEDURE generate_monthly_report(
    p_year INTEGER,
    p_month INTEGER
)
LANGUAGE plpgsql AS $$
DECLARE
    v_report_id INTEGER;
    v_row RECORD;
BEGIN
    -- Создание записи отчёта
    INSERT INTO monthly_reports (year, month, generated_at, status)
    VALUES (p_year, p_month, NOW(), 'Генерация')
    RETURNING id INTO v_report_id;
    
    -- Заполнение данными
    FOR v_row IN
        SELECT 
            p.name AS product_name,
            SUM(od.quantity) AS total_quantity,
            SUM(od.quantity * od.price) AS total_revenue
        FROM order_detail od
        JOIN customer_order co ON od.order_id = co.id
        JOIN product p ON od.product_id = p.id
        WHERE EXTRACT(YEAR FROM co.order_date) = p_year
          AND EXTRACT(MONTH FROM co.order_date) = p_month
        GROUP BY p.name
    LOOP
        INSERT INTO monthly_report_details 
            (report_id, product_name, quantity, revenue)
        VALUES (v_report_id, v_row.product_name, v_row.total_quantity, v_row.total_revenue);
    END LOOP;
    
    -- Обновление статуса
    UPDATE monthly_reports SET status = 'Готов' WHERE id = v_report_id;
END;
$$;

-- =============================================
-- Таблица отчётов
-- =============================================
CREATE TABLE IF NOT EXISTS monthly_reports (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    generated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'Генерация'
);

CREATE TABLE IF NOT EXISTS monthly_report_details (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES monthly_reports(id) ON DELETE CASCADE,
    product_name VARCHAR(200),
    quantity INTEGER,
    revenue DECIMAL(12, 2)
);
```

#### Часть 2. GUI-панель автоматизации

2. Создать форму `automation_panel.ui` и приложение `automation_app.py`:

Требования к интерфейсу:
- Вкладка «Расчёт стоимости заказа» — ввод ID заказа → результат
- Вкладка «Создание заказа» — форма с выбором клиента, продуктов, количества
- Вкладка «Генерация отчёта» — выбор года и месяца → кнопка «Сгенерировать»
- Вкладка «Триггеры» — список триггеров и их статус
- Таблица результатов для каждой операции
- Лог выполнения процедур

#### Часть 3. Модуль вызова процедур

3. Создать модуль `procedure_caller.py`:

```python
import psycopg2
from typing import List, Dict, Optional

class ProcedureCaller:
    """Вызов хранимых процедур и функций PostgreSQL"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def calculate_order(self, order_id: int) -> List[Dict]:
        """Вызов функции calculate_order_total"""
        query = "SELECT * FROM calculate_order_total(%s)"
        return self._execute_function(query, (order_id,))
    
    def create_order(self, customer_id: int, products: List[int],
                     quantities: List[int]) -> int:
        """Вызов функции create_customer_order"""
        products_str = "{" + ",".join(str(p) for p in products) + "}"
        quantities_str = "{" + ",".join(str(q) for q in quantities) + "}"
        
        query = """SELECT create_customer_order(%s, %s::INTEGER[], %s::INTEGER[])"""
        
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (customer_id, products_str, quantities_str))
                return cur.fetchone()[0]
    
    def generate_report(self, year: int, month: int):
        """Вызов процедуры generate_monthly_report"""
        query = "CALL generate_monthly_report(%s, %s)"
        
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (year, month))
                conn.commit()
    
    def get_reports(self) -> List[Dict]:
        """Получить список отчётов"""
        query = """
        SELECT id, year, month, generated_at, status
        FROM monthly_reports
        ORDER BY year DESC, month DESC;
        """
        return self._execute_query(query)
    
    def get_report_details(self, report_id: int) -> List[Dict]:
        """Получить детали отчёта"""
        query = """
        SELECT product_name, quantity, revenue
        FROM monthly_report_details
        WHERE report_id = %s;
        """
        return self._execute_query(query, (report_id,))
    
    def _execute_function(self, query: str, params: tuple) -> List[Dict]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
                return []
    
    def _execute_query(self, query: str, params=None) -> List[Dict]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Хранимая функция расчёта стоимости заказа | 5,00 |
| Триггер автоматического обновления order_total | 4,00 |
| Функция создания заказа с массивами | 4,00 |
| Процедура генерации月度 отчёта | 4,00 |
| Таблицы для хранения отчётов | 3,00 |
| GUI-панель вызова процедур | 3,00 |
| Модуль вызова процедур из Python | 2,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- SQL-файл с процедурами
- Таблицы из инвариантной части

### Инструкция для администратора ЦПДЭ

1. Убедиться, что PostgreSQL запущен.
2. Применить SQL-файл с процедурами.

### Инструкция для технического эксперта

1. Подготовить SQL-файл `procedures/business_logic.sql`.
2. Проверить работоспособность PostgreSQL.
