"""
Модуль API для получения заметок из базы данных.
Стоматология «Улыбка» — Задание 5
Демонстрационный экзамен (КИМ 09.02.07-5-2027)

Что такое FastAPI?
------------------
FastAPI — это современный Python-фреймворк для создания веб-API.
Он позволяет быстро создавать REST-серверы с автоматической документацией.

Как запустить этот сервер?
--------------------------
1. Убедитесь, что установлены зависимости:
   pip install fastapi uvicorn psycopg2-binary

2. Запустите сервер:
   python src/api_server.py

3. Откройте браузер:
   - Документация: http://127.0.0.1:8000/docs
   - API: http://127.0.0.1:8000/api/notes

Что делает этот API?
--------------------
Эндпоинт GET /api/notes возвращает все заметки из таблицы «notes»
в формате JSON с преобразованием данных:
- id — идентификатор заметки
- title_user — заголовок + логин пользователя (например: "Конференция ИТ - user25")
- content — содержание заметки
- formatted_date — дата в формате ДД.ММ.ГГГГ (например: "15.03.2027")
"""

# ==================== ИМПОРТ НЕОБХОДИМЫХ БИБЛИОТЕК ====================

# Импорт FastAPI — основного класса для создания веб-API
# FastAPI автоматически создаёт документацию в формате OpenAPI
from fastapi import FastAPI, HTTPException, Query

# Импорт psycopg2 — библиотеки для работы с PostgreSQL
import psycopg2
from psycopg2.extras import RealDictCursor

# Импорт типов данных из Python для типизации
from typing import List, Optional, Dict, Any
from datetime import datetime

# Импорт os для работы с переменными окружения
import os

# ==================== НАСТРОЙКИ ПРИЛОЖЕНИЯ ====================

# Создаём экземпляр приложения FastAPI
# title — название, которое появится в документации
# version — версия API
app = FastAPI(
    title="API Заметок — Стоматология Улыбка",
    description="API для получения заметок из базы данных PostgreSQL",
    version="1.0.0"
)

# ==================== НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ ====================
# Параметры подключения к PostgreSQL
# В продакшене используйте переменные окружения!
DB_CONFIG = {
    "host": "localhost",        # Адрес сервера БД
    "port": 5432,               # Порт PostgreSQL
    "database": "stomatologiya", # Имя базы данных
    "user": "postgres",         # Имя пользователя
    "password": "12345"         # Пароль
}


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_db_connection():
    """
    Создаёт подключение к базе данных PostgreSQL.
    
    Как это работает:
    1. psycopg2.connect() устанавливает соединение с БД
    2. cursor(cursor_factory=RealDictCursor) создаёт курсор,
       который возвращает данные как словари (по именам колонок)
    
    Returns:
        Кортеж (connection, cursor) — соединение и курсор
    
    Пример:
        conn, cur = get_db_connection()
        cur.execute("SELECT * FROM notes")
        results = cur.fetchall()
        cur.close()
        conn.close()
    """
    # Устанавливаем соединение с базой данных
    connection = psycopg2.connect(**DB_CONFIG)
    # Создаём курсор — объект для выполнения SQL-запросов
    # RealDictCursor возвращает каждую строку как словарь
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    return connection, cursor


def format_date(date_value):
    """
    Форматирует дату из формата PostgreSQL в формат ДД.ММ.ГГГГ.
    
    Args:
        date_value — объект datetime из PostgreSQL
    
    Returns:
        Строка в формате "DD.MM.YYYY"
        Например: "15.03.2027"
    
    Пример:
        >>> format_date(datetime(2027, 3, 15, 10, 30))
        "15.03.2027"
    """
    if date_value is None:
        return None
    # strftime() форматирует дату в строку
    # %d — день (01-31), %m — месяц (01-12), %Y — год
    return date_value.strftime("%d.%m.%Y")


# ==================== ЭНДПОИНТ GET /api/notes ====================

@app.get("/api/notes")
async def get_notes():
    """
    Получает все заметки из базы данных.
    
    Что делает этот метод:
    1. Подключается к базе данных PostgreSQL
    2. Выполняет SQL-запрос, который:
       - Выбирает все поля из таблицы notes
       - Объединяет (JOIN) с таблицей users для получения логина
       - Формирует поле title_user: "{title} - {login}"
    3. Форматирует дату в ДД.ММ.ГГГГ
    4. Возвращает JSON-ответ
    
    SQL-запрос:
        SELECT 
            n.id,
            n.title || ' - ' || u.login AS title_user,
            n.content,
            n.created_at
        FROM notes n
        LEFT JOIN users u ON n.id_user = u.id
    
    HTTP-статусы:
        200 OK — успешно, возвращает список заметок (или пустой массив [])
        500 Internal Server Error — ошибка подключения к БД
    
    Пример ответа:
        [
            {
                "id": 1,
                "title_user": "Конференция ИТ - user25",
                "content": "Не забыть подготовить презентацию...",
                "formatted_date": "15.03.2027"
            },
            ...
        ]
    """
    # ==================== ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ ====================
    connection = None
    cursor = None
    
    try:
        # Подключаемся к базе данных
        connection, cursor = get_db_connection()
        
        # Выполняем SQL-запрос
        # LEFT JOIN — соединяет notes с users, даже если пользователя нет
        query = """
            SELECT 
                n.id,
                n.title,
                u.login,
                n.content,
                n.created_at
            FROM notes n
            LEFT JOIN users u ON n.id_user = u.id
            ORDER BY n.id
        """
        
        # Выполняем запрос
        cursor.execute(query)
        
        # Получаем все результаты
        rows = cursor.fetchall()
        
        # Преобразуем результаты в формат, требуемый API
        notes = []
        for row in rows:
            # Формируем title_user: "{title} - {login}"
            # Если login NULL (пользователь удалён) — используем "unknown"
            login = row["login"] if row["login"] else "unknown"
            title_user = f"{row['title']} - {login}"
            
            # Форматируем дату
            formatted_date = format_date(row["created_at"])
            
            # Добавляем заметку в список
            notes.append({
                "id": row["id"],
                "title_user": title_user,
                "content": row["content"],
                "formatted_date": formatted_date
            })
        
        # Возвращаем результат
        # Если notes пустой — это нормально, возвращаем []
        # FastAPI автоматически преобразует список в JSON
        return notes
        
    except psycopg2.OperationalError as e:
        # Ошибка подключения к базе данных
        # Например: PostgreSQL не запущен, неверный пароль, база не найдена
        # Возвращаем HTTP 500 с сообщением об ошибке
        raise HTTPException(
            status_code=500,
            detail={"error": "Ошибка подключения к базе данных", "details": str(e)}
        )
    
    except psycopg2.ProgrammingError as e:
        # Ошибка SQL: таблица не найдена, поле не существует
        # Например: таблица «notes» ещё не создана
        raise HTTPException(
            status_code=500,
            detail={"error": "Ошибка структуры базы данных", "details": str(e)}
        )
    
    except Exception as e:
        # Любая другая непредвиденная ошибка
        raise HTTPException(
            status_code=500,
            detail={"error": "Внутренняя ошибка сервера", "details": str(e)}
        )
    
    finally:
        # Всегда закрываем соединение с БД
        # Даже если произошла ошибка — это важно!
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ==================== ЭНДПОИНТ ДЛЯ ПРОВЕРКИ РАБОТОСПОСОБНОСТИ ====================

@app.get("/")
async def root():
    """
    Корневой эндпоинт для проверки работоспособности сервера.
    
    Возвращает JSON с информацией о сервере.
    
    Пример ответа:
        {
            "message": "API Стоматология Улыбка работает!",
            "version": "1.0.0"
        }
    """
    return {
        "message": "API Стоматология Улыбка работает!",
        "version": "1.0.0"
    }


# ==================== ЗАПУСК СЕРВЕРА ====================

# Этот блок выполняется только при прямом запуске файла
# python src/api_server.py
if __name__ == "__main__":
    """
    Запускает сервер FastAPI.
    
    uvicorn — это ASGI-сервер для FastAPI.
    
    Параметры:
        --host 0.0.0.0 — сервер доступен по всем сетевым интерфейсам
        --port 8000 — порт, на котором рабо��ает сервер
        --reload — автоматическая перезагрузка при изменении кода
                   (удобно для разработки, но не для продакшена)
    
    После запуска:
        1. Откройте http://127.0.0.1:8000/docs — интерактивная документация
        2. Откройте http://127.0.0.1:8000/api/notes — список заметок
    """
    import uvicorn
    
    uvicorn.run(
        "src.api_server:app",  # Модуль:экземпляр (src.api_server:app)
        host="0.0.0.0",        # Доступен по всем IP
        port=8000,              # Порт 8000
        reload=True             # Автоперезагрузка при изменении кода
    )
