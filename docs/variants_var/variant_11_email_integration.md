# ВАРИАНТ 11: Интеграция с внешними API (почтовые сервисы)

---

## Задание

Разработать модуль интеграции информационной системы с внешним SMTP-сервером для отправки уведомлений и отчётов по электронной почте.

### Цель

Оценка умения выполнять интеграцию модулей в программное обеспечение, организовывать заданную интеграцию на базе имеющейся архитектуры.

### Исходные данные

Таблица `users` содержит поле `email`. Таблица `customer_order` содержит заказы с клиентами.

### Требования к выполнению

#### Часть 1. Модуль почтовой интеграции

1. Создать модуль `email_integration.py`:

```python
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import psycopg2

@dataclass
class EmailConfig:
    """Конфигурация SMTP-сервера"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str = "noreply@example.com"
    password: str = "app_password"
    use_tls: bool = True
    sender_name: str = "ИС Производства"

@dataclass
class EmailMessage:
    """Сообщение для отправки"""
    to_addresses: List[str]
    subject: str
    body_html: str
    body_text: Optional[str] = None
    attachments: Optional[List[str]] = None

class EmailIntegration:
    """Интеграция с внешним SMTP-сервером"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self._sent_log = []
    
    def send_message(self, message: EmailMessage) -> Dict:
        """Отправка одного сообщения"""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.config.sender_name} <{self.config.username}>"
            msg["To"] = ", ".join(message.to_addresses)
            msg["Subject"] = message.subject
            
            if message.body_text:
                msg.attach(MIMEText(message.body_text, "plain"))
            msg.attach(MIMEText(message.body_html, "html"))
            
            # Прикрепление файлов
            if message.attachments:
                for filepath in message.attachments:
                    self._attach_file(msg, filepath)
            
            # Отправка
            context = ssl.create_default_context()
            with smtplib.SMTP(
                self.config.smtp_server, 
                self.config.smtp_port
            ) as server:
                server.ehlo()
                if self.config.use_tls:
                    server.starttls(context=context)
                server.ehlo()
                server.login(self.config.username, self.config.password)
                server.sendmail(
                    self.config.username,
                    message.to_addresses,
                    msg.as_string()
                )
            
            # Логирование
            self._sent_log.append({
                "timestamp": datetime.now().isoformat(),
                "to": message.to_addresses,
                "subject": message.subject,
                "status": "sent"
            })
            
            return {"status": "sent", "message_id": len(self._sent_log)}
            
        except smtplib.SMTPAuthenticationError:
            return {"status": "error", "message": "Ошибка авторизации SMTP"}
        except smtplib.SMTPException as e:
            return {"status": "error", "message": f"SMTP-ошибка: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Ошибка отправки: {str(e)}"}
    
    def send_order_confirmation(self, customer_email: str, 
                                 order_id: int, total: float) -> Dict:
        """Отправка подтверждения заказа"""
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2c3e50;">Подтверждение заказа</h2>
            <p>Уважаемый клиент!</p>
            <p>Ваш заказ <strong>#{order_id}</strong> принят в обработку.</p>
            <table border="1" cellpadding="8" style="border-collapse: collapse;">
                <tr>
                    <td><strong>Номер заказа</strong></td>
                    <td>#{order_id}</td>
                </tr>
                <tr>
                    <td><strong>Сумма</strong></td>
                    <td>{total:,.2f} ₽</td>
                </tr>
                <tr>
                    <td><strong>Дата</strong></td>
                    <td>{datetime.now().strftime('%d.%m.%Y %H:%M')}</td>
                </tr>
            </table>
            <p>Спасибо за заказ!</p>
        </body>
        </html>
        """
        
        return self.send_message(EmailMessage(
            to_addresses=[customer_email],
            subject=f"Заказ #{order_id} подтверждён",
            body_html=html_body,
            body_text=f"Заказ #{order_id} на сумму {total:,.2f} ₽ принят."
        ))
    
    def send_bulk_notifications(self, user_ids: List[int],
                                 subject: str, template_vars: Dict) -> Dict:
        """Массовая рассылка пользователям"""
        results = []
        
        try:
            with psycopg2.connect(**self._get_db_params()) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, email, name FROM users WHERE id = ANY(%s)",
                        (user_ids,)
                    )
                    users = cur.fetchall()
            
            for user_id, email, name in users:
                if not email:
                    results.append({"user_id": user_id, "status": "skipped", "reason": "Нет email"})
                    continue
                
                template_vars_copy = template_vars.copy()
                template_vars_copy["name"] = name
                
                html = self._render_template(subject, template_vars_copy)
                
                result = self.send_message(EmailMessage(
                    to_addresses=[email],
                    subject=subject,
                    body_html=html
                ))
                
                results.append({
                    "user_id": user_id,
                    "email": email,
                    "status": result["status"]
                })
            
            return {"total": len(results), "sent": sum(1 for r in results if r["status"] == "sent"), "results": results}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _attach_file(self, msg: MIMEMultipart, filepath: str):
        """Прикрепление файла к сообщению"""
        try:
            with open(filepath, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(filepath)}"
            )
            msg.attach(part)
        except Exception as e:
            raise Exception(f"Ошибка прикрепления файла {filepath}: {e}")
    
    def _render_template(self, subject: str, vars_dict: Dict) -> str:
        """Простая шаблонизация"""
        body = f"""
        <html><body style="font-family: Arial;">
        <h2>{subject}</h2>
        <p>Здравствуйте, {vars_dict.get('name', 'Клиент')}!</p>
        {vars_dict.get('content', '')}
        <p>С уважением, ИС Производства</p>
        </body></html>
        """
        return body
    
    def get_sent_log(self, limit: int = 50) -> List[Dict]:
        """Получить журнал отправленных писем"""
        return self._sent_log[-limit:]
    
    def _get_db_params(self) -> dict:
        return {
            "dbname": "demo_exam",
            "user": "postgres",
            "host": "localhost",
            "port": "5432"
        }
```

#### Часть 2. API-эндпоинты для email

2. Создать Flask-маршруты `api/email_routes.py`:

```python
from flask import Blueprint, request, jsonify
from email_integration import EmailIntegration, EmailConfig, EmailMessage

email_bp = Blueprint("email", __name__)
email_service = EmailIntegration(EmailConfig())

@email_bp.route("/api/email/send", methods=["POST"])
def send_email():
    """Отправка email-сообщения"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Отсутствует тело запроса"}), 400
    
    to_addresses = data.get("to")
    if not to_addresses or not isinstance(to_addresses, list):
        return jsonify({"error": "Поле 'to' обязательно и должно быть массивом"}), 400
    
    subject = data.get("subject", "")
    body_html = data.get("body_html", "")
    
    if not subject or not body_html:
        return jsonify({"error": "Поля 'subject' и 'body_html' обязательны"}), 400
    
    result = email_service.send_message(EmailMessage(
        to_addresses=to_addresses,
        subject=subject,
        body_html=body_html
    ))
    
    if result["status"] == "sent":
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@email_bp.route("/api/email/confirm", methods=["POST"])
def confirm_order():
    """Отправка подтверждения заказа"""
    data = request.get_json()
    
    customer_email = data.get("customer_email")
    order_id = data.get("order_id")
    total = data.get("total")
    
    if not all([customer_email, order_id, total]):
        return jsonify({"error": "Необходимы: customer_email, order_id, total"}), 400
    
    result = email_service.send_order_confirmation(
        customer_email, order_id, total
    )
    
    if result["status"] == "sent":
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@email_bp.route("/api/email/log", methods=["GET"])
def get_email_log():
    """Журнал отправленных писем"""
    log = email_service.get_sent_log()
    return jsonify(log), 200
```

#### Часть 3. GUI-панель отправки

3. Создать форму `email_panel.ui` и приложение `email_app.py`:

Требования к интерфейсу:
- Поля: получатели (через запятую), тема, тело HTML
- Кнопка «Отправить»
- Таблица журнала отправленных писем
- Форма «Подтверждение заказа» (email, ID заказа, сумма)
- Кнопка «Тестовое письм��»

### Критерии оценивания

| Критерий | Баллы |
|----------|-------|
| Подключение к SMTP-серверу с TLS | 5,00 |
| Отправка HTML-сообщений | 4,00 |
| Подтверждение заказа с шаблоном | 4,00 |
| Массовая рассылка из БД | 4,00 |
| Flask API-эндпоинты с валидацией | 4,00 |
| GUI-панель отправки | 3,00 |
| Журнал отправленных писем | 1,00 |
| **ИТОГО** | **25,00** |

### Необходимые приложения

- **Mock SMTP-сервер** (встроенный в Python): `python -m smtpd -n -c DebuggingServer localhost:1025`
- Таблица `users` с полем `email`

### Инструкция для администратора ЦПДЭ

1. Запустить mock SMTP-сервер: `python -m smtpd -n -c DebuggingServer localhost:1025` (в отдельном терминале).
2. Убедиться, что таблица `users` имеет поле `email`.
3. В конфигурации EmailConfig указать `smtp_server="localhost"`, `smtp_port=1025`.

### Инструкция для технического эксперта

1. Запустить mock SMTP-сервер на каждом рабочем месте.
2. Убедиться, что библиотека `smtplib` доступна (стандартная библиотека Python).
