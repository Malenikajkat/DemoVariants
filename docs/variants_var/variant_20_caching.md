# ВАРИАНТ 20: Проектирование и реализация кэширования данных

---

## Задание

Разработать систему кэширования данных для снижения нагрузки на базу данных и ускорения работы информационной системы.

### Цель

Оценка умения выполнять интеграцию модулей в программное обеспечение, организовывать заданную интеграцию на базе имеющейся архитектуры.

### Исходные данные

Информационная система часто обращается к следующим данным:
- Список продуктов
- Информация о клиентах
- Статистика заказов
- Параметры системы

### Требования к выполнению

#### Часть 1. Система кэширования

1. Создать модуль `cache_manager.py`:

```python
import time
import json
import hashlib
from typing import Optional, Any, Dict, List
from collections import OrderedDict
from functools import wraps
import psycopg2

class CacheEntry:
    """Запись кэша"""
    def __init__(self, key: str, value: Any, ttl: int = 300):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl  # время жизни в секундах
        self.access_count = 0
    
    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl
    
    @property
    def remaining_ttl(self) -> int:
        return max(0, int(self.ttl - (time.time() - self.created_at)))


class InMemoryCache:
    """Кэш в памяти с алгоритмом LRU"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        entry = self._cache.get(key)
        
        if entry is None:
            self._stats["misses"] += 1
            return None
        
        if entry.is_expired:
            self.delete(key)
            self._stats["misses"] += 1
            return None
        
        # Перемещение в конец (самое свежее)
        self._cache.move_to_end(key)
        entry.access_count += 1
        self._stats["hits"] += 1
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Установка значения в кэш"""
        if key in self._cache:
            self._cache.move_to_end(key)
        
        self._cache[key] = CacheEntry(key, value, ttl or self.default_ttl)
        
        # Удаление старых записей при переполнении
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
            self._stats["evictions"] += 1
    
    def delete(self, key: str) -> bool:
        """Удаление записи из кэша"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self):
        """Очистка всего кэша"""
        self._cache.clear()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def cleanup_expired(self):
        """Удаление всех истекших записей"""
        expired_keys = [
            k for k, v in self._cache.items() if v.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Статистика кэша"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = round(
            self._stats["hits"] / total * 100, 1
        ) if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": f"{hit_rate}%"
        }


class DatabaseCache:
    """Кэширование запросов к базе данных"""
    
    def __init__(self, db_params: dict, cache: Optional[InMemoryCache] = None):
        self.db_params = db_params
        self.cache = cache or InMemoryCache(max_size=500, default_ttl=120)
        self._connection_cache: Dict[str, Any] = {}
    
    def cached_query(self, query: str, params: tuple = (),
                     ttl: int = 120, cache_key: Optional[str] = None) -> List[Dict]:
        """Выполнение запроса с кэшированием"""
        # Генерация ключа кэша
        if cache_key is None:
            cache_key = self._generate_cache_key(query, params)
        
        # Попытка получить из кэша
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Выполнение запроса к БД
        result = self._execute_query(query, params)
        
        # Сохранение в кэш
        self.cache.set(cache_key, result, ttl=ttl)
        
        return result
    
    def cached_scalar(self, query: str, params: tuple = (),
                      ttl: int = 120) -> Any:
        """Выполнение запроса с возвратом одного значения"""
        cache_key = self._generate_cache_key(query, params)
        
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        result = self._execute_scalar(query, params)
        self.cache.set(cache_key, result, ttl=ttl)
        
        return result
    
    def invalidate_pattern(self, pattern: str):
        """Инвалидация кэша по шаблону"""
        keys_to_delete = [
            k for k in self.cache._cache.keys()
            if pattern in k
        ]
        for key in keys_to_delete:
            self.cache.delete(key)
        return len(keys_to_delete)
    
    def invalidate_all(self):
        """Полная инвалидация кэша"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """Статистика кэша"""
        stats = self.cache.get_stats()
        stats["connection_cache_size"] = len(self._connection_cache)
        return stats
    
    def _generate_cache_key(self, query: str, params: tuple) -> str:
        """Генерация уникального ключа кэша"""
        raw = f"{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
    
    def _execute_query(self, query: str, params: tuple) -> List[Dict]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def _execute_scalar(self, query: str, params: tuple) -> Any:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()[0]


def cached(ttl: int = 60):
    """Декоратор кэширования результатов функции"""
    _function_cache: Dict[str, CacheEntry] = {}
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Генерация ключа
            key_data = f"{func.__name__}:{args}:{json.dumps(kwargs, sort_keys=True)}"
            cache_key = hashlib.md5(key_data.encode("utf-8")).hexdigest()
            
            entry = _function_cache.get(cache_key)
            if entry and not entry.is_expired:
                return entry.value
            
            result = func(*args, **kwargs)
            _function_cache[cache_key] = CacheEntry(cache_key, result, ttl)
            
            # Ограничение размера
            if len(_function_cache) > 200:
                oldest_key = next(iter(_function_cache))
                del _function_cache[oldest_key]
            
            return result
        return wrapper
    return decorator
```

#### Часть 2. GUI-панель кэша

2. Создать форму `cache_panel.ui` и приложение `cache_app.py`:

Требования к интерфейсу:
- Статистика кэша: размер, хиты, промахи,命中率
- Таблица содержимого кэша (ключ, значение, TTL, кол-во обращений)
- Кнопка «Очистить кэш»
- Кнопка «Удалить истекшие»
- Поле для ручной инвалидации по шаблону
- Кнопка «Тест производительности» (сравнение с/без кэша)
- Визуализация hit rate (прогресс-бар)

#### Часть 3. Тестирование производительности

3. Создать модуль `cache_benchmark.py`:

```python
import time
from cache_manager import DatabaseCache

class CacheBenchmark:
    """Тестирование производительности кэша"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def run_benchmark(self, query: str, iterations: int = 100) -> Dict:
        """Сравнение скорости с кэшем и без"""
        cache = DatabaseCache(self.db_params)
        
        # Без кэша
        start = time.time()
        for _ in range(iterations):
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    cur.fetchall()
        no_cache_time = time.time() - start
        
        # С кэшем (первый запрос — промах, последующие — хит)
        start = time.time()
        for _ in range(iterations):
            cache.cached_query(query)
        with_cache_time = time.time() - start
        
        speedup = round(no_cache_time / with_cache_time, 2) if with_cache_time > 0 else 0
        
        stats = cache.get_cache_stats()
        
        return {
            "query": query,
            "iterations": iterations,
            "no_cache_ms": round(no_cache_time * 1000, 2),
            "with_cache_ms": round(with_cache_time * 1000, 2),
            "speedup": f"{speedup}x",
            "cache_stats": stats
        }
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| LRU-кэш в памяти | 5,00 |
| Кэширование SQL-запросов | 5,00 |
| TTL и автоматическая инвалидация | 4,00 |
| Статистика кэша (hit rate) | 3,00 |
| Декоратор кэширования | 3,00 |
| Тест производительности | 3,00 |
| GUI-панель управления кэшем | 2,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- База данных PostgreSQL с таблицами из инвариантной части

### Инструкция для администратора ЦПДЭ

1. Убедиться, что PostgreSQL запущен.
2. Проверить наличие psycopg2.

### Инструкция для технического эксперта

1. Подготовить базу данных.
2. Проверить работоспособность psycopg2.
