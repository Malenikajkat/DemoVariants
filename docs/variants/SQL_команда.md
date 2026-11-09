-- Загрузка JSON из файла напрямую
INSERT INTO customer (name, inn, address, phone, customer_type)
SELECT 
    data->>'name',
    data->>'inn',
    data->>'addres',
    data->>'phone',
    data->>'type'
FROM jsonb_array_readfile('C:\Users\malen\PycharmProjects\proba\task2_db\Заказчики.json') AS data;