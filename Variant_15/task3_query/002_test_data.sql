-- ============================================
-- Тестовые данные для задания 3
-- Стоматология "Улыбка" (Вариант 15)
-- ============================================

-- Очищаем тестовые данные (если есть)
DELETE FROM customer_order_detail;
DELETE FROM customer_order;
DELETE FROM specification;
DELETE FROM cost_calculation;
DELETE FROM production_order_operation;
DELETE FROM production_order_material;
DELETE FROM production_order;
DELETE FROM price;
DELETE FROM user_account;
DELETE FROM customer;
DELETE FROM product;
DELETE FROM material;
DELETE FROM tech_operation;

-- Сброс последовательностей
ALTER SEQUENCE customer_id_seq RESTART WITH 1;
ALTER SEQUENCE product_id_seq RESTART WITH 1;
ALTER SEQUENCE material_id_seq RESTART WITH 1;
ALTER SEQUENCE tech_operation_id_seq RESTART WITH 1;
ALTER SEQUENCE price_id_seq RESTART WITH 1;
ALTER SEQUENCE user_account_id_seq RESTART WITH 1;
ALTER SEQUENCE customer_order_id_seq RESTART WITH 1;
ALTER SEQUENCE customer_order_detail_id_seq RESTART WITH 1;

-- ============================================
-- 1. Заказчики
-- ============================================
INSERT INTO customer (id, name, inn, address, phone, customer_type) VALUES
    (1, 'ООО "МедиСнаб"', NULL, 'г. Москва', '+79198634592', 'Поставщик'),
    (2, 'ИП Жуков Андрей Викторович', '7712345678', 'г. Москва, ул. Здоровья, 10', '+79884581555', 'Покупатель'),
    (3, 'ООО "ДентаМатериалы"', '4140784214', 'г. Санкт-Петербург, пр. Медицинский, 15', '+79882584546', 'Поставщик'),
    (4, 'ООО "ИмплантСистемы"', '5874045632', 'г. Казань, ул. Хирургическая, 22', '+79627486389', 'Поставщик'),
    (5, 'ИП Тарасова Елена Игоревна', '2629011278', 'г. Екатеринбург, ул. Мира, 77', '+79184572398', 'Покупатель'),
    (6, 'ООО "КерамикаДент"', '7798765432', 'г. Новосибирск, пр. Академический, 40', '+79234567890', 'Поставщик');

-- ============================================
-- 2. Продукция
-- ============================================
INSERT INTO product (id, code, name) VALUES
    (1, 'СУ-00000001', 'Керамическая коронка (E-max)'),
    (2, 'СУ-00000002', 'Виниров керамический'),
    (3, 'СУ-00000003', 'Имплантат Nobel Active');

-- ============================================
-- 3. Материалы
-- ============================================
INSERT INTO material (id, code, name) VALUES
    (1, 'СМ-00000001', 'Циркониевый абатмент'),
    (2, 'СМ-00000002', 'Керамическая масса E-max'),
    (3, 'СМ-00000003', 'Титановый имплантат Nobel Active'),
    (4, 'СМ-00000004', 'Костная пыль (остеоген)'),
    (5, 'СМ-00000005', 'Рассасывающаяся мембрана'),
    (6, 'СМ-00000006', 'Анестетик Ультракаин (1шт)'),
    (7, 'СМ-00000007', 'Фрезерный блок цирконий'),
    (8, 'СМ-00000008', 'Цемент цемент-стоун');

-- ============================================
-- 4. Технологические операции
-- ============================================
INSERT INTO tech_operation (id, code, name) VALUES
    (1, 'СО-00000001', 'Диагностика и планирование'),
    (2, 'СО-00000002', 'Хирургический этап'),
    (3, 'СО-00000003', 'Стоматологическое моделирование'),
    (4, 'СО-00000004', 'Фиксация и полировка');

-- ============================================
-- 5. Цены на материалы
-- ============================================
INSERT INTO price (id, item_id, item_type, name, price_value) VALUES
    (1, 1, 'material', 'Циркониевый абатмент', 3000.00),
    (2, 2, 'material', 'Керамическая масса E-max', 15000.00),
    (3, 3, 'material', 'Титановый имплантат Nobel Active', 27000.00),
    (4, 4, 'material', 'Костная пыль (остеоген)', 600.00),
    (5, 5, 'material', 'Рассасывающаяся мембрана', 800.00),
    (6, 6, 'material', 'Анестетик Ультракаин (1шт)', 200.00),
    (7, 7, 'material', 'Фрезерный блок цирконий', 2000.00),
    (8, 8, 'material', 'Цемент цемент-стоун', 150.00);

-- ============================================
-- 6. Цены на операции
-- ============================================
INSERT INTO price (id, item_id, item_type, name, price_value) VALUES
    (9, 1, 'operation', 'Диагностика и планирование', 8000.00),
    (10, 2, 'operation', 'Хирургический этап', 20000.00),
    (11, 3, 'operation', 'Стоматологическое моделирование', 14000.00),
    (12, 4, 'operation', 'Фиксация и полировка', 15000.00);

-- ============================================
-- 7. Спецификация для "Керамическая коронка (E-max)"
-- ============================================
INSERT INTO specification (product_id, material_id, quantity_per_unit, operation_id, time_norm) VALUES
    (1, 1, 1.000, 1, 0.5),   -- Циркониевый абатмент
    (1, 2, 0.300, 3, 2.0),   -- Керамическая масса E-max
    (1, 7, 0.100, NULL, NULL), -- Фрезерный блок цирконий
    (1, 8, 0.200, 4, 0.5);   -- Цемент цемент-стоун

-- ============================================
-- 8. Заказ покупателя № 14
-- ============================================
INSERT INTO customer_order (id, order_number, order_date, customer_id, executor) VALUES
    (1, '14', '2026-04-18', 2, 'Стоматология "Улыбка"');

-- ============================================
-- 9. Детали заказа покупателя № 14
-- ============================================
INSERT INTO customer_order_detail (customer_order_id, product_id, quantity, price, discount, total_sum) VALUES
    (1, 1, 6, 25000.00, 2500.00, 135000.00),  -- Керамическая коронка
    (1, 2, 4, 32000.00, 3200.00, 115200.00),  -- Виниров керамический
    (1, 3, 3, 55000.00, 5500.00, 148500.00);  -- Имплантат Nobel Active

-- ============================================
-- 10. Тестовые пользователи
-- ============================================
INSERT INTO user_account (login, password_hash, role, is_blocked) VALUES
    ('admin', 'admin123', 'Администратор', FALSE),
    ('user1', 'user123', 'Пользователь', FALSE),
    ('user2', 'user123', 'Пользователь', FALSE);

-- ============================================
-- Проверка вставленных данных
-- ============================================
SELECT '--- Заказчики ---' AS info;
SELECT id, name, customer_type FROM customer ORDER BY id;

SELECT '--- Продукция ---' AS info;
SELECT id, code, name FROM product ORDER BY id;

SELECT '--- Цены на материалы ---' AS info;
SELECT item_id, name, price_value FROM price WHERE item_type = 'material' ORDER BY item_id;

SELECT '--- Цены на операции ---' AS info;
SELECT item_id, name, price_value FROM price WHERE item_type = 'operation' ORDER BY item_id;

SELECT '--- Заказ № 14 ---' AS info;
SELECT id, order_number, order_date, customer_id FROM customer_order;

SELECT '--- Детали заказа № 14 ---' AS info;
SELECT cod.id, pr.name, cod.quantity, cod.price, cod.discount, cod.total_sum
FROM customer_order_detail cod
JOIN product pr ON pr.id = cod.product_id
WHERE cod.customer_order_id = 1;
