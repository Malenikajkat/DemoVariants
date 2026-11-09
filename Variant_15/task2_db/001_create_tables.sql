-- ============================================
-- Скрипт создания базы данных
-- Стоматология "Улыбка" (Вариант 15)
-- Задание 2: Разработка базы данных
-- ============================================

-- Что такое SQL?
-- SQL (Structured Query Language) — это язык для работы с базами данных.
-- С его помощью мы создаём таблицы, добавляем данные, запрашиваем информацию.

-- Что такое база данных?
-- База данных — это organised хранилище информации.
-- Представьте себе Excel, но более мощный и надёжный.
-- В Excel у вас один лист, в базе данных — много таблиц, связанных между собой.

-- Что такое таблица?
-- Таблица — это как лист в Excel: строки и столбцы.
-- Например, таблица "customer" (покупатели) будет хранить информацию о клиентах.

-- ============================================
-- ОЧИСТКА СУЩЕСТВУЮЩИХ ТАБЛИЦ
-- ============================================
-- Эти команды удаляют таблицы, если они уже существуют.
-- Зачем это нужно? Чтобы можно было запустить скрипт несколько раз без ошибок.

-- CASCADE означает "удалить всё, что связано с этой таблицей"
-- Например, если есть таблица, которая ссылается на customer_order,
-- то при удалении customer_order CASCADE удалит и её.

-- Порядок удаления важен: сначала удаляем таблицы, которые зависят от других
DROP TABLE IF EXISTS customer_order_detail CASCADE;
DROP TABLE IF EXISTS customer_order CASCADE;
DROP TABLE IF EXISTS production_order_operation CASCADE;
DROP TABLE IF EXISTS production_order_material CASCADE;
DROP TABLE IF EXISTS production_order CASCADE;
DROP TABLE IF EXISTS specification CASCADE;
DROP TABLE IF EXISTS cost_calculation CASCADE;
DROP TABLE IF EXISTS price CASCADE;
DROP TABLE IF EXISTS user_account CASCADE;
DROP TABLE IF EXISTS customer CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS material CASCADE;
DROP TABLE IF EXISTS tech_operation CASCADE;

-- ============================================
-- 1. ТАБЛИЦА customer (Заказчик)
-- ============================================
-- Эта таблица хранит информацию о клиентах: поставщиках и покупателях.
-- Представьте себе карточки клиентов в папке.

CREATE TABLE customer (
    -- id — уникальный номер клиента (автоматически увеличивается: 1, 2, 3...)
    -- SERIAL — это автоинкремент (автоматически увеличивает на 1)
    -- PRIMARY KEY — это уникальный идентификатор (как номер паспорта)
    id SERIAL PRIMARY KEY,
    
    -- name — название компании или ФИО (обязательное поле)
    -- VARCHAR(200) — это текст до 200 символов
    -- NOT NULL — это поле обязательно должно быть заполнено
    name VARCHAR(200) NOT NULL,
    
    -- inn — ИНН организации (уникальный номер, как номер паспорта)
    -- UNIQUE — означает, что два клиента не могут иметь одинаковый ИНН
    inn VARCHAR(20) UNIQUE,
    
    -- address — адрес клиента (необязательное поле)
    -- Если поле не обязательно, можно оставить пустым
    address VARCHAR(300),
    
    -- phone — телефон клиента
    phone VARCHAR(20),
    
    -- customer_type — тип клиента: "Поставщик" или "Покупатель"
    -- CHECK — это ограничение: значение должно быть одним из перечисленных
    customer_type VARCHAR(50) NOT NULL CHECK (customer_type IN ('Поставщик', 'Покупатель'))
);

-- Пример данных, которые будут в этой таблице:
-- id | name              | inn          | address              | phone         | customer_type
-- ---|-------------------|--------------|----------------------|---------------|--------------
-- 1  | ООО "МедиСнаб"    | NULL         | г. Москва            | +7919...      | Поставщик
-- 2  | ИП Жуков А.В.     | 7712345678   | г. Москва, ул. ...   | +7988...      | Покупатель

-- ============================================
-- 2. ТАБЛИЦА product (Продукция)
-- ============================================
-- Эта таблица хранит информацию о продукции стоматологии.
-- Например: коронки, виниры, имплантаты.

CREATE TABLE product (
    id SERIAL PRIMARY KEY,           -- Уникальный номер продукции
    code VARCHAR(50) UNIQUE NOT NULL, -- Код продукции (например: "СУ-00000001")
    name VARCHAR(200) NOT NULL        -- Название продукции (например: "Керамическая коронка")
);

-- Пример данных:
-- id | code         | name
-- ---|--------------|---------------------------
-- 1  | СУ-00000001  | Керамическая коронка (E-max)
-- 2  | СУ-00000002  | Виниров керамический

-- ============================================
-- 3. ТАБЛИЦА material (Материалы)
-- ============================================
-- Эта таблица хранит информацию о материалах, которые используются для производства.
-- Например: циркониевые абатменты, керамическая масса, имплантаты.

CREATE TABLE material (
    id SERIAL PRIMARY KEY,           -- Уникальный номер материала
    code VARCHAR(50) UNIQUE NOT NULL, -- Код материала (например: "СМ-00000001")
    name VARCHAR(200) NOT NULL        -- Название материала
);

-- Пример данных:
-- id | code         | name
-- ---|--------------|---------------------------
-- 1  | СМ-00000001  | Циркониевый абатмент
-- 2  | СМ-00000002  | Керамическая масса E-max

-- ============================================
-- 4. ТАБЛИЦА tech_operation (Технологическая операция)
-- ============================================
-- Эта таблица хранит информацию о технологических операциях.
-- Например: диагностика, хирургический этап, моделирование.

CREATE TABLE tech_operation (
    id SERIAL PRIMARY KEY,           -- Уникальный номер операции
    code VARCHAR(50) UNIQUE NOT NULL, -- Код операции (например: "СО-00000001")
    name VARCHAR(200) NOT NULL        -- Название операции
);

-- Пример данных:
-- id | code         | name
-- ---|--------------|---------------------------
-- 1  | СО-00000001  | Диагностика и планирование
-- 2  | СО-00000002  | Хирургический этап

-- ============================================
-- 5. ТАБЛИЦА price (Цены)
-- ============================================
-- Эта таблица хранит цены на материалы и операции.
-- item_type указывает, к чему относится цена: "material" или "operation".

CREATE TABLE price (
    id SERIAL PRIMARY KEY,                    -- Уникальный номер записи
    item_id INTEGER NOT NULL,                 -- ID материала или операции
    item_type VARCHAR(20) NOT NULL CHECK (item_type IN ('material', 'operation')),
    name VARCHAR(200) NOT NULL,               -- Название (для удобства)
    price_value NUMERIC(12, 2) NOT NULL CHECK (price_value > 0)  -- Цена (число с 2 знаками после запятой)
);

-- NUMERIC(12, 2) — это число до 12 цифр, из которых 2 после запятой (например: 123456789012.34)
-- CHECK (price_value > 0) — цена должна быть больше нуля

-- Пример данных:
-- id | item_id | item_type | name                 | price_value
-- ---|---------|-----------|----------------------|------------
-- 1  | 1       | material  | Циркониевый абатмент | 3000.00
-- 9  | 1       | operation | Диагностика          | 8000.00

-- ============================================
-- 6. Т��БЛИЦА user_account (Пользователь)
-- ============================================
-- Эта таблица хранит информацию о пользователях системы.
-- Например: администраторы и обычные пользователи.

CREATE TABLE user_account (
    id SERIAL PRIMARY KEY,              -- Уникальный номер пользователя
    login VARCHAR(50) UNIQUE NOT NULL,  -- Логин для входа (уникальный)
    password_hash VARCHAR(255) NOT NULL, -- Хеш пароля (зашифрованный пароль)
    role VARCHAR(20) NOT NULL CHECK (role IN ('Администратор', 'Пользователь')),
    is_blocked BOOLEAN DEFAULT FALSE,   -- Заблокирован ли пользователь (FALSE = нет)
    created_at TIMESTAMP DEFAULT NOW()  -- Дата создания (автоматически: NOW() = текущее время)
);

-- BOOLEAN — это логический тип: TRUE (истина) или FALSE (ложь)
-- DEFAULT FALSE — если не указано другое значение, будет FALSE
-- DEFAULT NOW() — автоматически установит текущую дату и время

-- Пример данных:
-- id | login | password_hash | role          | is_blocked | created_at
-- ---|-------|---------------|---------------|------------|-------------------
-- 1  | admin | admin123      | Администратор | FALSE      | 2024-01-01 10:00:00

-- ============================================
-- 7. ТАБЛИЦА customer_order (Заказ покупателя)
-- ============================================
-- Эта таблица хранит заказы от покупателей.
-- customer_id — это ссылка на таблицу customer (кто сделал заказ).

CREATE TABLE customer_order (
    id SERIAL PRIMARY KEY,                    -- Уникальный номер заказа
    order_number VARCHAR(50) UNIQUE NOT NULL, -- Номер заказа (например: "14")
    order_date DATE NOT NULL,                 -- Дата заказа
    customer_id INTEGER NOT NULL,             -- ID покупателя (ссылка на таблицу customer)
    executor VARCHAR(100) NOT NULL,           -- Исполнитель (кто выполняет заказ)
    
    -- FOREIGN KEY — это ссылка на другую таблицу
    -- REFERENCES customer(id) — ссылается на таблицу customer, столбец id
    -- ON UPDATE CASCADE — если id в customer изменится, обновится и здесь
    -- ON DELETE RESTRICT — нельзя удалить клиента, если у него есть заказы
    CONSTRAINT fk_customer_order_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- FOREIGN KEY — это связь между таблицами.
-- Например: customer_order.customer_id ссылается на customer.id.
-- Это означает: "этот заказ принадлежит этому покупателю".

-- Пример данных:
-- id | order_number | order_date | customer_id | executor
-- ---|--------------|------------|-------------|---------------------------
-- 1  | 14           | 2026-04-18 | 2           | Стоматология "Улыбка"

-- ============================================
-- 8. ТАБЛИЦА customer_order_detail (Детали заказа)
-- ============================================
-- Эта таблица хранит позиции заказа (какая продукция и в каком количестве).
-- customer_order_id — ссылка на заказ, product_id — ссылка на продукцию.

CREATE TABLE customer_order_detail (
    id SERIAL PRIMARY KEY,                  -- Уникальный номер записи
    customer_order_id INTEGER NOT NULL,     -- ID заказа (ссылка на customer_order)
    product_id INTEGER NOT NULL,            -- ID продукции (ссылка на product)
    quantity NUMERIC(10, 3) NOT NULL CHECK (quantity > 0),  -- Количество
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),       -- Цена за единицу
    discount NUMERIC(12, 2) DEFAULT 0 CHECK (discount >= 0),-- Скидка
    total_sum NUMERIC(12, 2) NOT NULL,     -- Итоговая сумма (количество × цена - скидка)
    
    -- Ссылки на другие таблицы
    CONSTRAINT fk_order_detail_order FOREIGN KEY (customer_order_id) 
        REFERENCES customer_order(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_order_detail_product FOREIGN KEY (product_id) 
        REFERENCES product(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ON DELETE CASCADE — если заказ удалён, удалить и все детали
-- ON DELETE RESTRICT — нельзя удалить продукцию, если она есть в заказах

-- Пример данных:
-- id | customer_order_id | product_id | quantity | price   | discount | total_sum
-- ---|-------------------|------------|----------|---------|----------|----------
-- 1  | 1                 | 1          | 6.000    | 25000.00| 2500.00  | 135000.00

-- ============================================
-- 9. ТАБЛИЦА production_order (Заказ на производство)
-- ============================================
-- Эта таблица хранит заказы на производство продукции.
-- product_id — ссылка на продукцию, которую нужно произвести.

CREATE TABLE production_order (
    id SERIAL PRIMARY KEY,                -- Уникальный номер заказа
    order_number VARCHAR(50) UNIQUE NOT NULL, -- Номер заказа
    order_date DATE NOT NULL,             -- Дата заказа
    subdivision VARCHAR(100),             -- Подразделение (например: "Ортопедическое отделение")
    executor VARCHAR(100),                -- Исполнитель
    product_id INTEGER NOT NULL,          -- ID продукции (ссылка на product)
    CONSTRAINT fk_production_order_product FOREIGN KEY (product_id) 
        REFERENCES product(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Пример данных:
-- id | order_number | order_date | subdivision          | executor     | product_id
-- ---|--------------|------------|----------------------|--------------|------------
-- 1  | 14           | 2026-04-19 | Ортопедическое отд.  | Администратор| 1

-- ============================================
-- 10. ТАБЛИЦА production_order_material (Материалы производства)
-- ============================================
-- Эта таблица хранит материалы, которые нужны для производства.
-- production_order_id — ссылка на заказ производства, material_id — ссылка на материал.

CREATE TABLE production_order_material (
    id SERIAL PRIMARY KEY,                     -- Уникальный номер записи
    production_order_id INTEGER NOT NULL,      -- ID заказа производства (ссылка)
    material_id INTEGER NOT NULL,              -- ID материала (ссылка)
    quantity NUMERIC(10, 3) NOT NULL CHECK (quantity > 0), -- Количество
    CONSTRAINT fk_prod_order_material_order FOREIGN KEY (production_order_id) 
        REFERENCES production_order(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_prod_order_material_material FOREIGN KEY (material_id) 
        REFERENCES material(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Пример данных:
-- id | production_order_id | material_id | quantity
-- ---|---------------------|-------------|---------
-- 1  | 1                   | 1           | 6.000

-- ============================================
-- 11. ТАБЛИЦА production_order_operation (Операции производства)
-- ============================================
-- Эта таблица хранит операции, которые нужно выполнить для производства.
-- production_order_id — ссылка на заказ производства, operation_id — ссылка на операцию.

CREATE TABLE production_order_operation (
    id SERIAL PRIMARY KEY,                         -- Уникальный номер записи
    production_order_id INTEGER NOT NULL,          -- ID заказа производства (ссылка)
    operation_id INTEGER NOT NULL,                 -- ID операции (ссылка)
    duration_hours NUMERIC(5, 2) NOT NULL CHECK (duration_hours > 0), -- Время в часах
    CONSTRAINT fk_prod_order_operation_order FOREIGN KEY (production_order_id) 
        REFERENCES production_order(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_prod_order_operation_operation FOREIGN KEY (operation_id) 
        REFERENCES tech_operation(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Пример данных:
-- id | production_order_id | operation_id | duration_hours
-- ---|---------------------|--------------|----------------
-- 1  | 1                   | 1            | 2.00

-- ============================================
-- 12. ТАБЛИЦА specification (Спецификация)
-- ============================================
-- Эта таблица хранит состав изделия (какие материалы и операции нужны для продукции).
-- product_id — ссылка на продукцию, material_id — ссылка на материал, operation_id — ссылка на операцию.

CREATE TABLE specification (
    id SERIAL PRIMARY KEY,                     -- Уникальный номер записи
    product_id INTEGER NOT NULL,               -- ID продукции (ссылка)
    material_id INTEGER NOT NULL,              -- ID материала (ссылка)
    quantity_per_unit NUMERIC(10, 3) NOT NULL CHECK (quantity_per_unit > 0), -- Норма расхода на единицу
    operation_id INTEGER,                      -- ID операции (может быть NULL)
    time_norm NUMERIC(5, 2) CHECK (time_norm >= 0), -- Норма времени
    CONSTRAINT fk_specification_product FOREIGN KEY (product_id) 
        REFERENCES product(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_specification_material FOREIGN KEY (material_id) 
        REFERENCES material(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_specification_operation FOREIGN KEY (operation_id) 
        REFERENCES tech_operation(id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- Пример данных:
-- id | product_id | material_id | quantity_per_unit | operation_id | time_norm
-- ---|------------|-------------|-------------------|--------------|----------
-- 1  | 1          | 1           | 1.000             | NULL         | NULL

-- ============================================
-- 13. ТАБЛИЦА cost_calculation (Расчёт стоимости)
-- ============================================
-- Эта таблица хранит расчёт себестоимости продукции.
-- product_id — ссылка на продукцию, material_id — ссылка на материал, operation_id — ссылка на операцию.

CREATE TABLE cost_calculation (
    id SERIAL PRIMARY KEY,                 -- Уникальный номер записи
    product_id INTEGER NOT NULL,           -- ID продукции (ссылка)
    material_id INTEGER NOT NULL,          -- ID материала (ссылка)
    operation_id INTEGER NOT NULL,         -- ID операции (ссылка)
    quantity NUMERIC(10, 3) NOT NULL CHECK (quantity > 0), -- Количество
    total_sum NUMERIC(12, 2) NOT NULL,     -- Итоговая сумма
    CONSTRAINT fk_cost_calc_product FOREIGN KEY (product_id) 
        REFERENCES product(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_cost_calc_material FOREIGN KEY (material_id) 
        REFERENCES material(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_cost_calc_operation FOREIGN KEY (operation_id) 
        REFERENCES tech_operation(id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- Пример данных:
-- id | product_id | material_id | operation_id | quantity | total_sum
-- ---|------------|-------------|--------------|----------|----------
-- 1  | 1          | 1           | 1            | 6.000    | 135000.00

-- ============================================
-- ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ ЗАПРОСОВ
-- ============================================
-- Индекс — это как оглавление в книге.
-- Без индекса база данных ищет данные перебором всех строк.
-- С индексом база данных находит данные быстро, как по оглавлению.

-- CREATE INDEX — создаёт индекс
-- idx_... — название индекса (idx = index)
-- ON table(column) — индекс создаётся для столбца column в таблице table

CREATE INDEX idx_customer_order_customer ON customer_order(customer_id);
CREATE INDEX idx_customer_order_detail_order ON customer_order_detail(customer_order_id);
CREATE INDEX idx_customer_order_detail_product ON customer_order_detail(product_id);
CREATE INDEX idx_production_order_product ON production_order(product_id);
CREATE INDEX idx_production_order_material_order ON production_order_material(production_order_id);
CREATE INDEX idx_production_order_material_material ON production_order_material(material_id);
CREATE INDEX idx_production_order_operation_order ON production_order_operation(production_order_id);
CREATE INDEX idx_production_order_operation_operation ON production_order_operation(operation_id);
CREATE INDEX idx_specification_product ON specification(product_id);
CREATE INDEX idx_specification_material ON specification(material_id);
CREATE INDEX idx_specification_operation ON specification(operation_id);
CREATE INDEX idx_cost_calculation_product ON cost_calculation(product_id);
CREATE INDEX idx_cost_calculation_material ON cost_calculation(material_id);
CREATE INDEX idx_cost_calculation_operation ON cost_calculation(operation_id);
CREATE INDEX idx_price_item ON price(item_type, item_id);

-- ============================================
-- КОММЕНТАРИИ К ТАБЛИЦАМ
-- ============================================
-- COMMENT ON TABLE — добавляет описание к таблице
-- Это полезно для других разработчиков, чтобы понять, зачем нужна таблица

COMMENT ON TABLE customer IS 'Заказчики (поставщики и покупатели)';
COMMENT ON TABLE product IS 'Готовая продукция';
COMMENT ON TABLE material IS 'Сырьё и материалы';
COMMENT ON TABLE tech_operation IS 'Технологические операции производства';
COMMENT ON TABLE price IS 'Прайс-лист на материалы и операции';
COMMENT ON TABLE user_account IS 'Пользователи системы';
COMMENT ON TABLE customer_order IS 'Заказы покупателей';
COMMENT ON TABLE customer_order_detail IS 'Позици�� заказа покупателя';
COMMENT ON TABLE production_order IS 'Заказы на производство';
COMMENT ON TABLE production_order_material IS 'Материалы для производства';
COMMENT ON TABLE production_order_operation IS 'Операции для производства';
COMMENT ON TABLE specification IS 'Спецификация изделия (состав и нормы)';
COMMENT ON TABLE cost_calculation IS 'Расчёт себестоимости продукции';
