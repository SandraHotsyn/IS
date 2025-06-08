from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# Підключення шрифту
font_path = os.path.join("static", "fonts", "FreeSans.ttf")
pdfmetrics.registerFont(TTFont("FreeSans", font_path))

def generate_order_pdf(order):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40

    # Назва
    p.setFont("FreeSans", 16)
    p.drawString(50, y, "TechPoint — Інтернет-магазин техніки")

    p.setFont("FreeSans", 10)
    p.drawRightString(width - 50, y, f"№ замовлення: {order.id}")
    y -= 15
    p.drawRightString(width - 50, y, f"Дата: {order.date.strftime('%d.%m.%Y %H:%M')}")
    y -= 30

    # Дані клієнта
    p.setFont("FreeSans", 12)
    p.drawString(50, y, f"Ім’я покупця: {order.customer.name}")
    y -= 20
    p.drawString(50, y, f"Телефон: {order.customer.phone}")
    y -= 20
    p.drawString(50, y, f"Email: {order.customer.email}")
    y -= 20
    p.drawString(50, y, f"Адреса доставки: {order.customer.address}")
    y -= 40

    # Список товарів
    p.setFont("FreeSans", 12)
    p.drawString(50, y, "Список товарів:")
    y -= 20
    for item in order.items:
        text = f"• {item.product.name} — {item.quantity} × {item.unit_price:.2f} грн = {item.quantity * item.unit_price:.2f} грн"
        p.drawString(60, y, text)
        y -= 20

    # Сума
    y -= 10
    p.setFont("FreeSans", 12)
    p.drawString(50, y, f"Загальна сума: {order.total:.2f} грн")
    y -= 40

    # Дякуємо
    p.setFont("FreeSans", 12)
    p.drawString(50, y, "💙 Дякуємо за покупку! Сподіваємося бачити вас знову.")
    y -= 40

    # Контакти магазину
    p.setFont("FreeSans", 10)
    p.drawString(50, y, "Контакти магазину:")
    y -= 15
    p.drawString(60, y, "📞 Телефон: +380 96 123 45 67")
    y -= 15
    p.drawString(60, y, "📧 Email: support@techpoint.ua")
    y -= 40

    # Дата внизу
    p.setFont("FreeSans", 8)
    p.drawRightString(width - 50, 30, f"Надруковано: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
