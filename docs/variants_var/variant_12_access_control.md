# ВАРИАНТ 12: Настройка прав доступа и ролевой модели

---

## Задание

Разработать систему расширенного управления правами доступа с ролевой моделью, гранулярными разрешениями и аудитом изменений прав.

### Цель

Оценка умения разрабатывать подсистемы безопасности информационной системы в соответствии с техническим заданием.

### Исходные данные

Базовая таблица `users` с ролями «Администратор» и «Пользователь». Требуется расширить модель до детализированной системы прав.

### Требования к выполнению

#### Часть 1. Ролевая модель и права доступа

1. Создать модуль `access_control.py`:

```python
import psycopg2
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Permission:
    """Разрешение (право)"""
    code: str           # Например: "orders:view", "users:delete"
    description: str    # Описание
    category: str       # Категория: orders, users, products, settings

@dataclass
class Role:
    """Роль"""
    name: str
    permissions: List[Permission] = field(default_factory=list)

class AccessControlSystem:
    """Система управления правами доступа"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
        self._cache_roles = {}
    
    def create_role(self, role_name: str, 
                    permissions: List[str]) -> bool:
        """Создание новой роли с разрешениями"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    # Проверка существования
                    cur.execute(
                        "SELECT COUNT(*) FROM roles WHERE name = %s",
                        (role_name,)
                    )
                    if cur.fetchone()[0] > 0:
                        return False  # Роль уже существует
                    
                    cur.execute(
                        "INSERT INTO roles (name, created_at) VALUES (%s, NOW())",
                        (role_name,)
                    )
                    
                    # Добавление разрешений
                    for perm_code in permissions:
                        cur.execute(
                            """INSERT INTO role_permissions (role_name, permission_code)
                               VALUES (%s, %s)""",
                            (role_name, perm_code)
                        )
                    
                    conn.commit()
                    self._invalidate_cache()
                    return True
        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Ошибка создания роли: {str(e)}")
    
    def assign_role_to_user(self, user_id: int, role_name: str) -> bool:
        """Назначение роли пользователю"""
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO user_roles (user_id, role_name, assigned_at)
                           VALUES (%s, %s, NOW())
                           ON CONFLICT (user_id, role_name) 
                           DO UPDATE SET assigned_at = NOW()""",
                        (user_id, role_name)
                    )
                    
                    # Запись в аудит
                    cur.execute(
                        """INSERT INTO access_audit 
                           (user_id, action, details, changed_at)
                           VALUES (%s, 'role_assigned', %s, NOW())""",
                        (user_id, f"Роль '{role_name}' назначена")
                    )
                    
                    conn.commit()
                    return True
        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Ошибка назначения роли: {str(e)}")
    
    def check_permission(self, user_id: int, 
                         permission_code: str) -> bool:
        """Проверка наличия разрешения у пользователя"""
        user_roles = self._get_user_roles(user_id)
        
        for role_name in user_roles:
            role = self._get_role_permissions(role_name)
            for perm in role.permissions:
                if perm.code == permission_code:
                    return True
        
        return False
    
    def get_user_permissions(self, user_id: int) -> List[Dict]:
        """Получить все разрешения пользователя"""
        user_roles = self._get_user_roles(user_id)
        all_permissions = []
        
        for role_name in user_roles:
            role = self._get_role_permissions(role_name)
            for perm in role.permissions:
                all_permissions.append({
                    "permission_code": perm.code,
                    "description": perm.description,
                    "category": perm.category,
                    "from_role": role_name
                })
        
        return all_permissions
    
    def get_access_audit(self, user_id: Optional[int] = None, 
                         days: int = 7) -> List[Dict]:
        """Журнал изменений прав доступа"""
        query = """
        SELECT 
            aa.user_id,
            u.login,
            aa.action,
            aa.details,
            aa.changed_at
        FROM access_audit aa
        JOIN users u ON aa.user_id = u.id
        WHERE aa.changed_at > NOW() - INTERVAL '%s days'
        """
        params = [days]
        
        if user_id is not None:
            query += " AND aa.user_id = %s"
            params.append(user_id)
        
        query += " ORDER BY aa.changed_at DESC"
        
        return self._execute_query(query, tuple(params))
    
    def _get_user_roles(self, user_id: int) -> List[str]:
        """Получить роли пользователя (с кэшированием)"""
        if user_id not in self._cache_roles:
            try:
                with psycopg2.connect(**self.db_params) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT role_name FROM user_roles WHERE user_id = %s",
                            (user_id,)
                        )
                        self._cache_roles[user_id] = [
                            row[0] for row in cur.fetchall()
                        ]
            except Exception:
                self._cache_roles[user_id] = []
        
        return self._cache_roles.get(user_id, [])
    
    def _get_role_permissions(self, role_name: str) -> Role:
        """Получить роли и разрешения (с кэшированием)"""
        if role_name not in self._cache_roles:
            try:
                with psycopg2.connect(**self.db_params) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """SELECT p.code, p.description, p.category
                               FROM role_permissions rp
                               JOIN permissions p ON rp.permission_code = p.code
                               WHERE rp.role_name = %s""",
                            (role_name,)
                        )
                        perms = [
                            Permission(
                                code=row[0],
                                description=row[1],
                                category=row[2]
                            )
                            for row in cur.fetchall()
                        ]
                        self._cache_roles[role_name] = Role(
                            name=role_name,
                            permissions=perms
                        )
            except Exception:
                self._cache_roles[role_name] = Role(name=role_name)
        
        return self._cache_roles[role_name]
    
    def _invalidate_cache(self):
        """Очистка кэша ролей"""
        self._cache_roles.clear()
    
    def _execute_query(self, query: str, params=None) -> List[Dict]:
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
```

#### Часть 2. SQL-схема расширенных прав

2. Создать `migrations/004_access_control.sql`:

```sql
-- Таблица разрешений
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL
);

-- Предзаполнение разрешений
INSERT INTO permissions (code, description, category) VALUES
('orders:view', 'Просмотр заказов', 'orders'),
('orders:create', 'Создание заказов', 'orders'),
('orders:edit', 'Редактирование заказов', 'orders'),
('orders:delete', 'Удаление заказов', 'orders'),
('users:view', 'Просмотр пользователей', 'users'),
('users:create', 'Создание пользователей', 'users'),
('users:edit', 'Редактирование пользователей', 'users'),
('users:delete', 'Удаление пользователей', 'users'),
('settings:view', 'Просмотр настроек', 'settings'),
('settings:edit', 'Изменение настроек', 'settings');

-- Таблица ролей
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Связь ролей и разрешений
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) REFERENCES roles(name) ON DELETE CASCADE,
    permission_code VARCHAR(50) REFERENCES permissions(code) ON DELETE CASCADE,
    UNIQUE(role_name, permission_code)
);

-- Назначение ролей пользователям
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_name VARCHAR(50) REFERENCES roles(name) ON DELETE SET NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, role_name)
);

-- Аудит изменений прав
CREATE TABLE IF NOT EXISTS access_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    details TEXT,
    changed_at TIMESTAMP DEFAULT NOW()
);

-- Назначение прав по умолчанию
INSERT INTO roles (name) VALUES ('Администратор'), ('Пользователь');

-- Администратор: все права
INSERT INTO role_permissions (role_name, permission_code)
SELECT 'Администратор', code FROM permissions;

-- Пользователь: только просмотр
INSERT INTO role_permissions (role_name, permission_code)
SELECT 'Пользователь', code FROM permissions WHERE code LIKE '%:view';
```

#### Часть 3. GUI-менеджер прав

3. Создать форму `access_manager.ui` и приложение `access_app.py`:

Требования к ��нтерфейсу:
- Таблица пользователей с колонкой «Роль»
- Выпадающий список для назначения ролей
- Дерево разрешений по категориям
- Чекбоксы для управления разрешениями роли
- Вкладка «Журнал аудита»
- Кнопка «Проверить права» для выбранного пользователя

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Создание ролей и назначение разрешений | 5,00 |
| Назначение ролей пользователям | 4,00 |
| Проверка прав (check_permission) | 4,00 |
| Кэширование ролей и разрешений | 3,00 |
| Журнал аудита изменений | 4,00 |
| GUI-менеджер прав | 4,00 |
| Обработка исключений, комментарии | 1,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- SQL-миграция расширенных прав
- Таблица `users` из инвариантной части

### Инструкция для администратора ЦПДЭ

1. Убедиться, что PostgreSQL запущен.
2. Подготовить SQL-миграцию.

### Инструкция для технического эксперта

1. Применить SQL-миграцию к базе данных.
2. Проверить доступность psycopg2.
