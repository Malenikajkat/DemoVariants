-- ============================================
-- Задание 3: Создание запроса
-- Стоматология "Улыбка" (Вариант 15)
-- Расчёт полной стоимости заказа покупателя
-- ============================================

-- Формула расчёта:
-- Полная_стоимость = Σ(Количество_продукции × 
--     (Σ(Норма_расхода_материала × Цена_материала) + 
--      Σ(Норма_времени_операции × Стоимость_операции)))

-- ============================================
-- Запрос: расчёт полной стоимости заказа
-- ============================================

WITH 
-- -------------------------------------------------------
-- Шаг 1: Расчёт стоимости материалов для каждой позиции
-- спецификации
-- -------------------------------------------------------
spec_materials AS (
    SELECT 
        s.product_id,
        s.material_id,
        s.quantity_per_unit,
        p.price_value AS material_price,
        s.quantity_per_unit * p.price_value AS line_material_cost
    FROM specification s
    JOIN price p ON p.item_id = s.material_id 
                 AND p.item_type = 'material'
),

-- -------------------------------------------------------
-- Шаг 2: Расчёт стоимости операций для каждой позиции
-- спецификации
-- -------------------------------------------------------
spec_operations AS (
    SELECT 
        s.product_id,
        s.operation_id,
        s.time_norm,
        p.price_value AS operation_price,
        s.time_norm * p.price_value AS line_operation_cost
    FROM specification s
    JOIN price p ON p.item_id = s.operation_id 
                 AND p.item_type = 'operation'
),

-- -------------------------------------------------------
-- Шаг 3: Агрегация стоимости материалов по продукту
-- -------------------------------------------------------
product_material_cost AS (
    SELECT 
        product_id,
        SUM(line_material_cost) AS total_material_cost
    FROM spec_materials
    GROUP BY product_id
),

-- -------------------------------------------------------
-- Шаг 4: Агрегация стоимости операций по продукту
-- -------------------------------------------------------
product_operation_cost AS (
    SELECT 
        product_id,
        SUM(line_operation_cost) AS total_operation_cost
    FROM spec_operations
    GROUP BY product_id
),

-- -------------------------------------------------------
-- Шаг 5: Расчёт стоимости позиции заказа
-- -------------------------------------------------------
order_line_calc AS (
    SELECT 
        co.id AS order_id,
        co.order_number,
        cod.id AS detail_id,
        cod.quantity,
        pr.name AS product_name,
        pmc.total_material_cost AS material_cost_per_unit,
        poc.total_operation_cost AS operation_cost_per_unit,
        -- Стоимость материалов на позицию
        cod.quantity * COALESCE(pmc.total_material_cost, 0) AS material_cost,
        -- Стоимость операций на позицию
        cod.quantity * COALESCE(poc.total_operation_cost, 0) AS operation_cost,
        -- Итого по позиции (с учётом скидки)
        cod.total_sum AS line_total
    FROM customer_order_detail cod
    JOIN customer_order co ON co.id = cod.customer_order_id
    JOIN product pr ON pr.id = cod.product_id
    LEFT JOIN product_material_cost pmc ON pmc.product_id = cod.product_id
    LEFT JOIN product_operation_cost poc ON poc.product_id = cod.product_id
),

-- -------------------------------------------------------
-- Шаг 6: Расчёт общей суммы заказа
-- -------------------------------------------------------
order_total_calc AS (
    SELECT 
        order_id,
        SUM(line_total) AS order_total
    FROM order_line_calc
    GROUP BY order_id
)

-- -------------------------------------------------------
-- ФИНАЛЬНЫЙ ВЫБОРКА
-- -------------------------------------------------------
SELECT 
    ol.order_id,
    ol.order_number,
    ol.product_name,
    ol.quantity,
    -- Расчётная стоимость материалов (без учёта скидки)
    ROUND(COALESCE(ol.material_cost, 0), 2) AS material_cost,
    -- Расчётная стоимость технологических операций (без учёта скидки)
    ROUND(COALESCE(ol.operation_cost, 0), 2) AS operation_cost,
    -- Итоговая стоимость позиции (с учётом скидки из заказа)
    ROUND(ol.line_total, 2) AS line_total,
    -- Общая сумма заказа
    ROUND(ot.order_total, 2) AS order_total
FROM order_line_calc ol
JOIN order_total_calc ot ON ot.order_id = ol.order_id
ORDER BY ol.order_id, ol.detail_id;
