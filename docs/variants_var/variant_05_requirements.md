# ВАРИАНТ 05: Анализ и формализация требований заказчика

---

## Задание

Разработать инструмент для сбора, анализа и формализации требований заказчика к информационной системе с визуализацией связей между требованиями.

### Цель

Оценка умения выполнять анализ предметной области, собирать и структурировать требования заказчика.

### Исходные данные

Заказчик предоставляет документ с требованиями в формате JSON:

```json
{
  "project_name": "ИС Производства",
  "requirements": [
    {
      "id": "REQ-001",
      "category": "Функциональные",
      "description": "Система должна поддерживать авторизацию пользователей",
      "priority": "Высокий",
      "status": "Принято",
      "related": ["REQ-002", "REQ-005"]
    },
    {
      "id": "REQ-002",
      "category": "Функциональные",
      "description": "Система должна поддерживать роли: Администратор, Пользователь",
      "priority": "Высокий",
      "status": "Принято",
      "related": ["REQ-001"]
    },
    {
      "id": "REQ-003",
      "category": "Нефункциональные",
      "description": "Время отклика API не более 200 мс",
      "priority": "Средний",
      "status": "На рассмотрении",
      "related": []
    },
    {
      "id": "REQ-004",
      "category": "Функциональные",
      "description": "Система должна поддерживать экспорт отчётов в PDF",
      "priority": "Низкий",
      "status": "Отклонено",
      "related": ["REQ-005"]
    },
    {
      "id": "REQ-005",
      "category": "Функциональные",
      "description": "Система должна поддерживать REST API для интеграции",
      "priority": "Высокий",
      "status": "Принято",
      "related": ["REQ-003", "REQ-004"]
    }
  ]
}
```

### Требования к выполнению

#### Часть 1. Модуль анализа требований

1. Создать модуль `requirement_analyzer.py`:

```python
import json
from typing import Dict, List, Optional
from collections import defaultdict

class RequirementAnalyzer:
    """Анализ и формализация требований заказчика"""
    
    def __init__(self, requirements_data: Dict):
        self.data = requirements_data
        self.project_name = requirements_data.get("project_name", "Без названия")
        self.requirements = requirements_data.get("requirements", [])
        self._index_requirements()
    
    def _index_requirements(self):
        """Индексация требований по ID для быстрого поиска"""
        self._by_id = {req["id"]: req for req in self.requirements}
        self._by_category = defaultdict(list)
        self._by_priority = defaultdict(list)
        self._by_status = defaultdict(list)
        
        for req in self.requirements:
            self._by_category[req["category"]].append(req)
            self._by_priority[req["priority"]].append(req)
            self._by_status[req["status"]].append(req)
    
    def get_by_id(self, req_id: str) -> Optional[Dict]:
        """Получить требование по ID"""
        return self._by_id.get(req_id)
    
    def get_by_category(self, category: str) -> List[Dict]:
        """Получить требования по категории"""
        return self._by_category.get(category, [])
    
    def get_by_priority(self, priority: str) -> List[Dict]:
        """Получить требования по приоритету"""
        return self._by_priority.get(priority, [])
    
    def get_related_requirements(self, req_id: str) -> List[Dict]:
        """Получить связанные требования"""
        req = self._by_id.get(req_id)
        if not req:
            return []
        related_ids = req.get("related", [])
        return [self._by_id[rid] for rid in related_ids if rid in self._by_id]
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Построить граф зависимостей между требованиями"""
        graph = {}
        for req in self.requirements:
            graph[req["id"]] = req.get("related", [])
        return graph
    
    def get_analysis_report(self) -> Dict:
        """Сформировать отчёт анализа требований"""
        total = len(self.requirements)
        return {
            "project_name": self.project_name,
            "total": total,
            "by_category": {
                cat: len(reqs) for cat, reqs in self._by_category.items()
            },
            "by_priority": {
                pri: len(reqs) for pri, reqs in self._by_priority.items()
            },
            "by_status": {
                status: len(reqs) for status, reqs in self._by_status.items()
            },
            "accepted_count": len(self._by_status.get("Принято", [])),
            "rejected_count": len(self._by_status.get("Отклонено", [])),
            "pending_count": len(self._by_status.get("На рассмотрении", [])),
            "acceptance_rate": round(
                len(self._by_status.get("Принято", [])) / total * 100, 1
            ) if total > 0 else 0
        }
    
    def validate_requirements(self) -> List[str]:
        """Валидация требований: проверка на полноту и корректность"""
        issues = []
        valid_priorities = {"Высокий", "Средний", "Низкий"}
        valid_statuses = {"Принято", "Отклонено", "На рассмотрении"}
        
        for req in self.requirements:
            if not req.get("id"):
                issues.append(f"Требование без ID: {req}")
            if req.get("priority") not in valid_priorities:
                issues.append(
                    f"Неверный приоритет для {req['id']}: {req.get('priority')}"
                )
            if req.get("status") not in valid_statuses:
                issues.append(
                    f"Неверный статус для {req['id']}: {req.get('status')}"
                )
            # Проверка связанных требований
            for related_id in req.get("related", []):
                if related_id not in self._by_id:
                    issues.append(
                        f"Ссылка на несуществующее требование: "
                        f"{req['id']} → {related_id}"
                    )
        
        return issues
```

#### Часть 2. GUI-приложение для работы с требованиями

2. Создать форму `requirements_viewer.ui` и приложение `requirements_app.py`:

Требования к интерфейсу:
- Загрузка файла с требованиями (JSON)
- Дерево требований с группировкой по категориям
- Таблица с фильтрацией по приоритету и статусу
- Панель деталей выбранного требования
- Визуализация графа зависимостей (линии связей)
- Кнопка «Валидация» для проверки корректности
- Область результатов валидации

#### Часть 3. Экспорт формализованных требований

3. Создать модуль `requirement_exporter.py`:

```python
import json
from requirement_analyzer import RequirementAnalyzer

class RequirementExporter:
    """Экспорт требований в различные форматы"""
    
    def __init__(self, analyzer: RequirementAnalyzer):
        self.analyzer = analyzer
    
    def export_to_json(self, filepath: str):
        """Экспорт в JSON с добавленной аналитикой"""
        report = self.analyzer.get_analysis_report()
        output = {
            "project_name": self.analyzer.project_name,
            "analysis": report,
            "requirements": self.analyzer.requirements
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    
    def export_to_text(self, filepath: str):
        """Экспорт в текстовый формат (ТЗ)"""
        report = self.analyzer.get_analysis_report()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"ТРЕБОВАНИЯ К СИСТЕМЕ: {self.analyzer.project_name}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Всего требований: {report['total']}\n")
            f.write(f"Принято: {report['accepted_count']}\n")
            f.write(f"На рассмотрении: {report['pending_count']}\n")
            f.write(f"Отклонено: {report['rejected_count']}\n")
            f.write(f"Процент принятия: {report['acceptance_rate']}%\n\n")
            
            for category, reqs in self.analyzer._by_category.items():
                f.write(f"\n--- {category} ---\n")
                for req in reqs:
                    f.write(f"  [{req['id']}] {req['description']}\n")
                    f.write(f"    Приоритет: {req['priority']}\n")
                    f.write(f"    Статус: {req['status']}\n")
```

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Реализован анализ требований (группировка, фильтрация, связи) | 5,00 |
| Построен граф зависимостей | 4,00 |
| Реализована валидация требований | 4,00 |
| Разработан GUI для просмотра и фильтрации | 6,00 |
| Реализован экспорт в JSON и текстовый формат | 4,00 |
| Обработка исключений, комментарии, именование | 2,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Файл `requirements.json` с требованиями заказчика

### Инструкция для администратора ЦПДЭ

1. Подготовить файл с требованиями заказчика.
2. Убедиться, что Python 3.10+ установлен.

### Инструкция для технического эксперта

1. Подготовить файл `requirements.json`.
2. Проверить работоспособность PyQt6.
