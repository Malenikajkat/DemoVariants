# ВАРИАНТ 19: Разработка модуля экспорта в PDF/Excel

---

## Задание

Разработать модуль генерации отчётов в форматах PDF и Excel с настраиваемыми шаблонами для информационной системы.

### Цель

Оценка умения производить разработку модулей информационной системы в соответствии с техническим заданием.

### Исходные данные

База данных PostgreSQL содержит таблицы: `customer_order`, `order_detail`, `product`, `customer`.

### Требования к выполнению

#### Часть 1. Экспорт в PDF

1. Создать модуль `pdf_report.py`:

```python
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import psycopg2
from datetime import datetime

class PDFReportGenerator:
    """Генератор отчётов в формате PDF"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def generate_order_report(self, order_id: int, filepath: str):
        """Генерация отчёта по заказу"""
        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Заголовок
        title_style = ParagraphStyle(
            "ReportTitle", parent=styles["Heading1"],
            fontSize=18, alignment=TA_CENTER, spaceAfter=20
        )
        story.append(Paragraph("ОТЧЁТ ПО ЗАКАЗУ", title_style))
        
        # Информация о заказе
        order_data = self._get_order_data(order_id)
        if not order_data:
            raise Exception(f"Заказ #{order_id} не найден")
        
        order, customer, details = order_data
        
        info_data = [
            ["Параметр", "Значение"],
            ["Номер заказа", f"#{order['id']}"],
            ["Дата", order["order_date"].strftime("%d.%m.%Y") if order["order_date"] else "-"],
            ["Статус", order["status"]],
            ["Клиент", customer["name"]],
            ["Телефон", customer.get("phone", "-")],
            ["Адрес", customer.get("address", "-")],
        ]
        
        t = Table(info_data, colWidths=[4*cm, 12*cm])
        t.setStyle(self._get_table_style())
        story.append(t)
        story.append(Spacer(1, 1*cm))
        
        # Позиции заказа
        story.append(Paragraph("Позиции заказа", styles["Heading2"]))
        
        items_data = [["№", "Наименование", "Кол-во", "Цена", "Сумма"]]
        for i, detail in enumerate(details, 1):
            items_data.append([
                str(i),
                detail["product_name"],
                str(detail["quantity"]),
                f"{detail['price']:,.2f} ₽",
                f"{detail['quantity'] * detail['price']:,.2f} ₽"
            ])
        
        # Итого
        total = sum(d["quantity"] * d["price"] for d in details)
        items_data.append([
            "", "", "", 
            Paragraph("<b>ИТОГО:</b>", styles["Normal"]),
            Paragraph(f"<b>{total:,.2f} ₽</b>", styles["Normal"])
        ])
        
        t = Table(items_data, colWidths=[1*cm, 7*cm, 2*cm, 3*cm, 3*cm])
        t.setStyle(self._get_table_style())
        story.append(t)
        
        # Подвал
        story.append(Spacer(1, 2*cm))
        footer_style = ParagraphStyle(
            "Footer", parent=styles["Normal"],
            fontSize=8, alignment=TA_CENTER, textColor=colors.grey
        )
        story.append(Paragraph(
            f"Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M')} | "
            f"ИС Производства",
            footer_style
        ))
        
        doc.build(story)
    
    def generate_sales_summary_report(self, filepath: str, 
                                        start_date: datetime = None,
                                        end_date: datetime = None):
        """Сводный отчёт по продажам"""
        doc = SimpleDocTemplate(
            filepath, pagesize=landscape(A4),
            rightMargin=1.5*cm, leftMargin=1.5*cm,
            topMargin=1.5*cm, bottomMargin=1.5*cm
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Заголовок
        story.append(Paragraph(
            "СВОДНЫЙ ОТЧЁТ ПО ПРОДАЖАМ",
            ParagraphStyle("Title", parent=styles["Heading1"], 
                          alignment=TA_CENTER, fontSize=16)
        ))
        
        period = f" ({start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')})" if start_date and end_date else ""
        story.append(Paragraph(
            f"Период:{period}",
            ParagraphStyle("Period", parent=styles["Normal"], 
                          alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 1*cm))
        
        # KPI
        kpi = self._get_sales_kpi(start_date, end_date)
        kpi_data = [
            ["Показатель", "Значение"],
            ["Всего заказов", str(kpi["total_orders"])],
            ["Общая выручка", f"{kpi['total_revenue']:,.2f} ₽"],
            ["Средний чек", f"{kpi['avg_order']:,.2f} ₽"],
            ["Топ-продукт", kpi["top_product"] or "-"],
        ]
        
        t = Table(kpi_data, colWidths=[5*cm, 7*cm])
        t.setStyle(self._get_table_style())
        story.append(t)
        story.append(Spacer(1, 1*cm))
        
        # Детализация по продуктам
        story.append(Paragraph("Детализация по продуктам", styles["Heading2"]))
        
        products = self._get_sales_by_product(start_date, end_date)
        items_data = [["№", "Продукт", "Кол-во", "Выручка", "% от общего"]]
        
        total_rev = kpi["total_revenue"] or 1
        for i, p in enumerate(products, 1):
            pct = round(p["total_revenue"] / total_rev * 100, 1)
            items_data.append([
                str(i), p["product_name"],
                str(p["total_quantity"]),
                f"{p['total_revenue']:,.2f} ₽",
                f"{pct}%"
            ])
        
        t = Table(items_data, colWidths=[1*cm, 6*cm, 2*cm, 3*cm, 2*cm])
        t.setStyle(self._get_table_style())
        story.append(t)
        
        doc.build(story)
    
    def _get_table_style(self):
        """Стиль таблицы"""
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    
    def _get_order_data(self, order_id: int):
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM customer_order WHERE id = %s",
                        (order_id,)
                    )
                    order_cols = [d[0] for d in cur.description]
                    order = dict(zip(order_cols, cur.fetchone()))
                    
                    cur.execute(
                        "SELECT * FROM customer WHERE id = %s",
                        (order["customer_id"],)
                    )
                    cust_cols = [d[0] for d in cur.description]
                    customer = dict(zip(cust_cols, cur.fetchone()))
                    
                    cur.execute(
                        """SELECT od.*, p.name AS product_name 
                           FROM order_detail od
                           JOIN product p ON od.product_id = p.id
                           WHERE od.order_id = %s""",
                        (order_id,)
                    )
                    det_cols = [d[0] for d in cur.description]
                    details = [dict(zip(det_cols, row)) for row in cur.fetchall()]
                    
                    return order, customer, details
        except Exception:
            return None
    
    def _get_sales_kpi(self, start_date=None, end_date=None):
        # Заглушка — реализовать запрос
        return {"total_orders": 0, "total_revenue": 0, 
                "avg_order": 0, "top_product": None}
    
    def _get_sales_by_product(self, start_date=None, end_date=None):
        return []
```

#### Часть 2. Экспорт в Excel

2. Создать модуль `excel_report.py`:

```python
import psycopg2
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

class ExcelReportGenerator:
    """Генератор отчётов в формате Excel"""
    
    def __init__(self, db_params: dict):
        self.db_params = db_params
    
    def generate_order_excel(self, order_id: int, filepath: str):
        """Экспорт заказа в Excel"""
        wb = Workbook()
        ws = wb.active
        ws.title = f"Заказ #{order_id}"
        
        # Стили
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
        title_font = Font(bold=True, size=14)
        total_font = Font(bold=True, size=11, color="C0392B")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )
        
        # Получение данных
        order, customer, details = self._get_order_data(order_id)
        
        # Заголовок
        ws.merge_cells("A1:F1")
        title_cell = ws["A1"]
        title_cell.value = f"Заказ #{order['id']}"
        title_cell.font = title_font
        title_cell.alignment = Alignment(horizontal="center")
        
        # Информация о клиенте
        ws.merge_cells("A3:B3")
        ws["A3"].value = "Клиент:"
        ws["A3"].font = Font(bold=True)
        ws["C3"].value = customer["name"]
        
        ws.merge_cells("A4:B4")
        ws["A4"].value = "Телефон:"
        ws["A4"].font = Font(bold=True)
        ws["C4"].value = customer.get("phone", "-")
        
        # Таблица позиций
        row = 6
        headers = ["№", "Наименование", "Кол-во", "Ед.", "Цена", "Сумма"]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center")
        
        total = 0
        for i, detail in enumerate(details, 1):
            row += 1
            sum_val = detail["quantity"] * detail["price"]
            total += sum_val
            
            values = [i, detail["product_name"], detail["quantity"],
                     detail.get("unit", "шт"), detail["price"], sum_val]
            
            for col_idx, val in enumerate(values, 1):
                cell = ws.cell(row=row, column=col_idx, value=val)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="center" if col_idx > 2 else "left")
        
        # Итого
        row += 2
        ws.merge_cells(f"A{row}:E{row}")
        total_cell = ws.cell(row=row, column=6, value=total)
        total_cell.value = f"ИТОГО: {total:,.2f} ₽"
        total_cell.font = total_font
        total_cell.fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid")
        
        # Автоширина столбцов
        for col in ws.columns:
            max_length = 0
            column_letter = get_column_letter(col[0].column)
            for cell in col:
                try:
                    max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[column_letter].width = min(max_length + 2, 30)
        
        wb.save(filepath)
    
    def _get_order_data(self, order_id: int):
        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM customer_order WHERE id = %s", (order_id,))
                order_cols = [d[0] for d in cur.description]
                order = dict(zip(order_cols, cur.fetchone()))
                
                cur.execute("SELECT * FROM customer WHERE id = %s", (order["customer_id"],))
                cust_cols = [d[0] for d in cur.description]
                customer = dict(zip(cust_cols, cur.fetchone()))
                
                cur.execute(
                    """SELECT od.*, p.name AS product_name 
                       FROM order_detail od
                       JOIN product p ON od.product_id = p.id
                       WHERE od.order_id = %s""",
                    (order_id,)
                )
                det_cols = [d[0] for d in cur.description]
                details = [dict(zip(det_cols, row)) for row in cur.fetchall()]
                
                return order, customer, details
```

#### Часть 3. GUI-генератор отчётов

3. Создать форму `report_generator.ui` и приложение `report_gen_app.py`:

Требования к интерфейсу:
- Вкладка «Отчёт по заказу (PDF)» — ввод ID заказа → генерация
- Вкладка «Отчёт по заказу (Excel)» — ввод ID заказа → генерация
- Вкладка «Сводный отчёт» — выбор периода → генерация PDF
- Поле для указания пути сохранения
- Прогресс-бар
- Кнопка «Открыть файл» после генерации

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Генерация PDF отчёта по заказу | 5,00 |
| Стилизация таблиц в PDF | 4,00 |
| Генерация Excel-отчёта со стилями | 5,00 |
| Автоширина столбцов в Excel | 3,00 |
| Сводный отчёт по продажам | 4,00 |
| Flask API для генерации отчётов | 3,00 |
| GUI-генератор с выбором формата | 3,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- Библиотеки: `reportlab`, `openpyxl`: `pip install reportlab openpyxl`
- Таблицы из инвариантной части

### Инструкция для администратора ЦПДЭ

1. Убедиться, что `reportlab` и `openpyxl` установлены.
2. Подготовить базу данных с данными.

### Инструкция для технического эксперта

1. Установить `reportlab` и `openpyxl`.
2. Проверить работоспособность PostgreSQL.
