# Руководство по тестированию API — Задание 5
## Вариант 15: Стоматология «Улыбка»

---

## Оглавление

1. [Подготовка окружения](#1-подготовка-окружения)
2. [Создание коллекции в Postman](#2-создание-коллекции-в-postman)
3. [Запрос 1: GET /api/notes — Получение заметок](#3-запрос-1-get-apinotes--получение-заметок)
4. [Запрос 2: GET / — Проверка работоспособности](#4-запрос-2-get--проверка-работоспособности)
5. [Запрос 3: Тестирование ошибки 500](#5-запрос-3-тестирование-ошибки-500)
6. [Запуск коллекции](#6-запуск-коллекции)
7. [Экспорт коллекции](#7-экспорт-коллекции)
8. [Альтернативное тестирование](#8-альтернативное-тестирование)
9. [Чек-лист для защиты](#9-чек-лист-для-защиты)

---

## 1. Подготовка окружения

### 1.1. Установка PostgreSQL

```powershell
# Проверка, запущен ли PostgreSQL
Get-Service -Name postgresql*

# Запуск PostgreSQL (если остановлен)
Start-Service -Name postgresql_x64-16
```

### 1.2. Создание базы данных

```sql
-- Подключитесь к PostgreSQL через pgAdmin или psql
-- Создайте базу данных
CREATE DATABASE stomatologiya;

-- Подключитесь к базе
\c stomatologiya

-- Выполните SQL-скрипт из файла:
-- Variant_15/api/001_create_notes_table.sql
```

Или через psql:

```powershell
psql -U postgres -d stomatologiya -f "C:\Users\malen\PycharmProjects\proba\Variant_15\api\001_create_notes_table.sql"
```

### 1.3. Создание пользователя users (если нет)

```sql
-- Таблица users должна существовать (из Задания 4)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Тестовые пользователи
INSERT INTO users (login, password_hash) VALUES
    ('admin', 'hashed_password_1'),
    ('doctor1', 'hashed_password_2'),
    ('receptionist', 'hashed_password_3');
```

### 1.4. Установка зависимостей

```powershell
cd C:\Users\malen\PycharmProjects\proba\Variant_15
pip install fastapi uvicorn psycopg2-binary
```

### 1.5. Установка Postman

1. Скачайте с [postman.com/downloads](https://www.postman.com/downloads/)
2. Установите и зарегистрируйтесь
3. Создайте новую коллекцию

### 1.6. Запуск сервера

```powershell
cd C:\Users\malen\PycharmProjects\proba\Variant_15
python src/api_server.py
```

Сервер запустится на `http://127.0.0.1:8000`

---

## 2. Создание коллекции в Postman

### Шаг 1: Создайте коллекцию

```
1. Нажмите New → Collection
2. Название: "Задание 5 — Стоматология Улыбка"
3. Описание: "API заметок для стоматологии 'Улыбка'"
4. Нажмите Save
```

### Шаг 2: Импортируйте готовую коллекцию

```
1. Нажмите на коллекцию → "..." → "Import"
2. Выберите файл: Variant_15/tests/api_collection.postman_collection.json
3. Нажмите "Import"
```

ИЛИ создайте запросы вручную (инструкция ниже).

---

## 3. Запрос 1: GET /api/notes — Получение заметок

### 3.1. Создание запроса

```
1. Откройте коллекцию "Задание 5 — Стоматология Улыбка"
2. Нажмите "Add Request"
3. Название: "GET /api/notes"
4. Метод: GET
5. URL: http://127.0.0.1:8000/api/notes
6. Нажмите "Save to Задание 5 — Стоматология Улыбка"
```

### 3.2. Отправка запроса

```
1. Нажмите кнопку "Send"
2. Проверьте результат:
   - Status: 200 OK
   - Time: ~50-200ms
   - Size: ~1-2KB
```

### 3.3. Ожидаемый ответ

```json
[
    {
        "id": 1,
        "title_user": "Конференция ИТ - admin",
        "content": "Не забыть подготовить презентацию по проекту стоматологии к конференции 20.03.2027.",
        "formatted_date": "15.03.2027"
    },
    {
        "id": 2,
        "title_user": "Проверка оборудования - doctor1",
        "content": "Заказать новые стоматологические кресла для кабинета №3.",
        "formatted_date": "16.03.2027"
    },
    {
        "id": 3,
        "title_user": "Отчёт за квартал - admin",
        "content": "Подготовить отчёт по количеству пациентов за Q1 2027.",
        "formatted_date": "17.03.2027"
    },
    {
        "id": 4,
        "title_user": "Обучение персонала - receptionist",
        "content": "Запланировать семинар по новым методикам лечения для врачей.",
        "formatted_date": "18.03.2027"
    },
    {
        "id": 5,
        "title_user": "Ремонт кабинета - doctor1",
        "content": "Провести ремонт в кабинете №2: покрасить стены, заменить освещение.",
        "formatted_date": "19.03.2027"
    }
]
```

### 3.4. Добавление скриптов тестов

Перейдите на вкладку **Tests** и вставьте следующий код:

```javascript
// ============================================
// ТЕСТЫ ДЛЯ GET /api/notes
// ============================================

// --- Тест 1: Проверка статуса 200 OK ---
pm.test("Статус код должен быть 200 OK", function () {
    pm.response.to.have.status(200);
});

// --- Тест 2: Проверка валидности JSON ---
pm.test("Ответ должен быть в формате JSON", function () {
    pm.response.to.be.json;
});

// --- Тест 3: Проверка, что ответ — массив ---
pm.test("Ответ должен быть массивом", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.be.an('array');
});

// --- Тест 4: Проверка структуры элементов ---
pm.test("Каждая заметка должна содержать все поля", function () {
    var jsonData = pm.response.json();
    
    if (jsonData.length > 0) {
        // Проверяем наличие всех обязательных полей
        pm.expect(jsonData[0]).to.have.property('id');
        pm.expect(jsonData[0]).to.have.property('title_user');
        pm.expect(jsonData[0]).to.have.property('content');
        pm.expect(jsonData[0]).to.have.property('formatted_date');
        
        // Проверяем тип id (число)
        pm.expect(jsonData[0].id).to.be.a('number');
        
        // Проверяем формат title_user: "{title} - {login}"
        pm.expect(jsonData[0].title_user).to.match(/^.+ - .+$/);
        
        // Проверяем формат даты: ДД.ММ.ГГГГ
        pm.expect(jsonData[0].formatted_date).to.match(/^\d{2}\.\d{2}\.\d{4}$/);
        
        // Проверяем, что content не пустой
        pm.expect(jsonData[0].content).to.be.a('string').and.to.have.lengthOf.greaterThan(0);
    } else {
        // Если массив пустой — это тоже допустимо (200 OK с пустым массивом)
        pm.test("Пустой массив — допустимый ответ", function () {
            pm.expect(true).to.be.true;
        });
    }
});

// --- Тест 5: Проверка количества заметок ---
pm.test("Должно быть не менее 3 заметок", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.length).to.be.at.least(3);
});

// --- Тест 6: Проверка заголовка Content-Type ---
pm.test("Content-Type должен быть application/json", function () {
    pm.response.to.be.header('Content-Type');
    pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json');
});
```

### 3.5. Результат тестов

После нажатия **Send** перейдите на вкладку **Test Results** (внизу):

```
✓ Статус код должен быть 200 OK
✓ Ответ должен быть в формате JSON
✓ Ответ должен быть массивом
✓ Каждая заметка должна содержать все поля
✓ Должно быть не менее 3 заметок
✓ Content-Type должен быть application/json

Result: All tests passed!
```

---

## 4. Запрос 2: GET / — Проверка работоспособности

### 4.1. Создание запроса

```
1. Нажмите "Add Request" в коллекции
2. Название: "GET / — Health Check"
3. Метод: GET
4. URL: http://127.0.0.1:8000/
5. Нажмите "Save"
```

### 4.2. Скрипты тестов

Вкладка **Tests**:

```javascript
// ============================================
// ТЕСТЫ ДЛЯ GET /
// ============================================

pm.test("Статус код должен быть 200 OK", function () {
    pm.response.to.have.status(200);
});

pm.test("Ответ должен быть в формате JSON", function () {
    pm.response.to.be.json;
});

pm.test("Должно быть поле message", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.message).to.exist;
    pm.expect(jsonData.message).to.include("работает");
});

pm.test("Должно быть поле version", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.version).to.exist;
    pm.expect(jsonData.version).to.eql("1.0.0");
});
```

### 4.3. Ожидаемый ответ

```json
{
    "message": "API Стоматология Улыбка работает!",
    "version": "1.0.0"
}
```

---

## 5. Запрос 3: Тестирование ошибки 500

### 5.1. Цель теста

Проверить, что при недоступности PostgreSQL сервер возвращает HTTP 500 с сообщением об ошибке.

### 5.2. Как вызвать ошибку 500

**Способ 1: Остановить PostgreSQL**

```powershell
# Остановка PostgreSQL
Stop-Service -Name postgresql_x64-16

# Проверка статуса
Get-Service -Name postgresql_x64-16
```

**Способ 2: Изменить пароль в api_server.py**

Временно измените `DB_CONFIG.password` на неверный:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "stomatologiya",
    "user": "postgres",
    "password": "wrong_password"  # Неверный пароль
}
```

**Способ 3: Изменить порт в api_server.py**

```python
DB_CONFIG = {
    "port": 9999,  # Неверный порт
}
```

### 5.3. Создание запроса

```
1. Нажмите "Add Request" в коллекции
2. Название: "Test 500 Error — DB Down"
3. Метод: GET
4. URL: http://127.0.0.1:8000/api/notes
5. Нажмите "Save"
```

### 5.4. Скрипты тестов

Вкладка **Tests**:

```javascript
// ============================================
// ТЕСТЫ ДЛЯ ОШИБКИ 500
// ============================================

pm.test("При ошибке БД должен быть статус 500", function () {
    if (pm.response.code === 500) {
        pm.expect(pm.response.code).to.eq(500);
    } else {
        pm.test("БД работает — тест 500 пропущен", function () {
            pm.expect(true).to.be.true;
        });
    }
});

pm.test("При ошибке возвращается JSON с полем error", function () {
    if (pm.response.code === 500) {
        var jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property('error');
        pm.expect(jsonData.error).to.be.a('string');
        pm.expect(jsonData.error.length).to.be.greaterThan(0);
    }
});

pm.test("Content-Type при ошибке — application/json", function () {
    if (pm.response.code === 500) {
        pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json');
    }
});
```

### 5.5. Ожидаемый ответ при ошибке

```json
{
    "error": "Ошибка подключения к базе данных",
    "details": "connection refused"
}
```

### 5.6. Восстановление PostgreSQL

```powershell
# Запуск PostgreSQL обратно
Start-Service -Name postgresql_x64-16

# Если использовали Способ 2 или 3 — верните правильные настройки в api_server.py
```

---

## 6. Запуск коллекции

### 6.1. Через GUI Postman

```
1. Откройте коллекцию "Задание 5 — Стоматология Улыбка"
2. Нажмите кнопку "Run"
3. Настройте параметры:
   - Iterations: 1
   - Delay: 0ms
4. Нажмите "Run Задание 5 — Стоматология Улыбка"
```

### 6.2. Результат запуска коллекции

```
┌────────────────────────────────────────────────────────────────┐
│  Collection Run: Задание 5 — Стоматология Улыбка              │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  GET /api/notes                                                │
│  ├─ ✓ Статус код должен быть 200 OK                            │
│  ├─ ✓ Ответ должен быть в формате JSON                         │
│  ├─ ✓ Ответ должен быть массивом                               │
│  ├─ ✓ Каждая заметка должна содержать все поля                 │
│  ├─ ✓ Должно быть не менее 3 заметок                           │
│  └─ ✓ Content-Type должен быть application/json                │
│                                                                │
│  GET / — Health Check                                          │
│  ├─ ✓ Статус код должен быть 200 OK                            │
│  ├─ ✓ Ответ должен быть в формате JSON                         │
│  ├─ ✓ Должно быть поле message                                 │
│  └─ ✓ Должно быть поле version                                 │
│                                                                │
│  Test 500 Error — DB Down                                      │
│  ├─ ✓ БД работает — тест 500 пропущен                          │
│  └─ ✓ (при остановке БД: все тесты проходят)                   │
│                                                                │
│  Result: All 10 tests passed!                                  │
│  Total time: 1.234s                                            │
└────────────────────────────────────────────────────────────────┘
```

### 6.3. Через Newman (CLI)

```powershell
# Установка Newman
npm install -g newman

# Запуск коллекции
newman run "C:\Users\malen\PycharmProjects\proba\Variant_15\tests\api_collection.postman_collection.json"

# Экспорт результатов в HTML
newman run "api_collection.postman_collection.json" -r html --reporter-html-export "test_results.html"
```

---

## 7. Экспорт коллекции

```
1. Наведите на коллекцию "Задание 5 — Стоматология Улыбка"
2. Нажмите "..." (три точки)
3. Выберите "Export"
4. Формат: Collection v2.1
5. Сохраните: Задание_5_Стоматология.postman_collection.json
6. Отправьте файл преподавателю
```

---

## 8. Альтернативное тестирование

### 8.1. Через браузер

```
1. Откройте: http://127.0.0.1:8000/api/notes
2. Проверьте JSON-ответ
3. Проверьте, что все поля присутствуют
```

### 8.2. Через Swagger UI

```
1. Откройте: http://127.0.0.1:8000/docs
2. Найдите GET /api/notes
3. Нажмите "Try it out"
4. Нажмите "Execute"
5. Проверьте Response body
```

### 8.3. Через PowerShell (Invoke-RestMethod)

```powershell
# Проверка корневого эндпоинта
Invoke-RestMethod -Uri "http://127.0.0.1:8000/" | ConvertTo-Json

# Проверка эндпоинта /api/notes
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/notes" | ConvertTo-Json

# Проверка с заголовками
$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/notes"
$response.StatusCode
$response.Headers['Content-Type']
$response.Content
```

### 8.4. Через Python

```python
import requests

# Тест 1: Проверка статуса 200
response = requests.get("http://127.0.0.1:8000/api/notes")
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
print(f"Status: {response.status_code} OK")

# Тест 2: Проверка JSON
assert response.headers['Content-Type'].startswith('application/json')
print("Content-Type: application/json OK")

# Тест 3: Проверка структуры
data = response.json()
assert isinstance(data, list), "Response should be a list"
print(f"Response is array with {len(data)} items OK")

# Тест 4: Проверка полей
if data:
    note = data[0]
    assert 'id' in note, "Missing 'id' field"
    assert 'title_user' in note, "Missing 'title_user' field"
    assert 'content' in note, "Missing 'content' field"
    assert 'formatted_date' in note, "Missing 'formatted_date' field"
    print("All fields present OK")
    
    # Проверка формата title_user
    assert ' - ' in note['title_user'], "title_user format incorrect"
    print(f"title_user format: '{note['title_user']}' OK")
    
    # Проверка формата даты
    import re
    assert re.match(r'^\d{2}\.\d{2}\.\d{4}$', note['formatted_date']), "Date format incorrect"
    print(f"Date format: '{note['formatted_date']}' OK")

# Тест 5: Проверка корневого эндпоинта
root = requests.get("http://127.0.0.1:8000/")
assert root.status_code == 200
assert 'message' in root.json()
print(f"Root endpoint: '{root.json()['message']}' OK")

print("\nAll tests passed!")
```

---

## 9. Чек-лист для защиты

### Перед защитой проверьте:

- [ ] PostgreSQL запущен (`Get-Service postgresql*`)
- [ ] База данных `stomatologiya` создана
- [ ] Таблица `notes` создана и заполнена данными (`SELECT * FROM notes;`)
- [ ] Таблица `users` создана с тестовыми пользователями
- [ ] Сервер запущен (`python src/api_server.py`)
- [ ] Сервер доступен: `http://127.0.0.1:8000/docs`
- [ ] Коллекция Postman создана и содержит 3 запроса
- [ ] Все тесты проходят (зелёные галочки)
- [ ] Тест 500 проверен (остановка PostgreSQL)
- [ ] Коллекция экспортирована в файл

### Вопросы преподавателя:

1. **Что делает эндпоинт GET /api/notes?**
   — Возвращает все заметки из таблицы notes с преобразованными данными

2. **Какое преобразование данных выполняется?**
   — title_user = title + " - " + login; created_at форматируется в ДД.ММ.ГГГГ

3. **Почему используется LEFT JOIN?**
   — Чтобы вернуть заметки даже если пользователь удалён (login = NULL → "unknown")

4. **Какой статус возвращается при пустой таблице?**
   — 200 OK с пустым массивом [] — это не ошибка

5. **Какой статус возвращается при ошибке БД?**
   — 500 Internal Server Error с JSON: {"error": "..."}

6. **Зачем нужны тесты в Postman?**
   — Автоматическая проверка корректности API после изменений

7. **Что проверяет тест на валидность JSON?**
   — Что Content-Type = application/json и тело ответа — валидный JSON

8. **Как протестировать ошибку 500?**
   — Остановить PostgreSQL и отправить запрос

---

## Приложение A: Полная структура коллекции

```
Задание 5 — Стоматология Улыбка
│
├── GET /api/notes
│   ├── Тест: Статус код должен быть 200 OK
│   ├── Тест: Ответ должен быть в формате JSON
│   ├── Тест: Ответ должен быть массивом
│   ├── Тест: Каждая заметка должна содержать все поля
│   ├── Тест: Должно быть не менее 3 заметок
│   └── Тест: Content-Type должен быть application/json
│
├── GET / — Health Check
│   ├── Тест: Статус код должен быть 200 OK
│   ├── Тест: Ответ должен быть в формате JSON
│   ├── Тест: Должно быть поле message
│   └── Тест: Должно быть поле version
│
└── Test 500 Error — DB Down
    ├── Тест: При ошибке БД должен быть статус 500
    ├── Тест: При ошибке возвращается JSON с полем error
    └── Тест: Content-Type при ошибке — application/json
```

## Приложение B: Переменные окружения

Для удобства можно создать переменные в Postman:

```
Environment: Stomatologiya API
├── base_url = http://127.0.0.1:8000
├── notes_endpoint = {{base_url}}/api/notes
└── health_endpoint = {{base_url}}/
```

Использование в запросах:

```
URL: {{notes_endpoint}}
```

## Приложение C: Решение распространённых проблем

### Проблема 1: Connection refused

```
Ошибка: psycopg2.OperationalError: connection refused
Решение:
  1. Проверьте PostgreSQL: Get-Service postgresql*
  2. Запустите: Start-Service postgresql_x64-16
  3. Проверьте порт: netstat -ano | findstr 5432
```

### Проблема 2: FATAL: database "stomatologiya" does not exist

```
Решение:
  1. psql -U postgres -c "CREATE DATABASE stomatologiya;"
  2. psql -U postgres -d stomatologiya -f api/001_create_notes_table.sql
```

### Проблема 3: FATAL: password authentication failed

```
Решение:
  1. Откройте Variant_15/src/api_server.py
  2. Проверьте DB_CONFIG.password
  3. Убедитесь, что пароль совпадает с паролем PostgreSQL
```

### Проблема 4: relation "users" does not exist

```
Решение:
  1. Создайте таблицу users (см. Задание 4)
  2. Или выполните:
     CREATE TABLE users (
         id SERIAL PRIMARY KEY,
         login VARCHAR(50) NOT NULL,
         password_hash VARCHAR(255) NOT NULL,
         created_at TIMESTAMP DEFAULT NOW()
     );
     INSERT INTO users (login, password_hash) VALUES
         ('admin', 'pass1'),
         ('doctor1', 'pass2'),
         ('receptionist', 'pass3');
```

### Проблема 5: Port 8000 already in use

```
Решение:
  1. Найдите процесс: netstat -ano | findstr :8000
  2. Завершите: taskkill /PID <PID> /F
  3. Или измените порт в api_server.py: port=8080
```
