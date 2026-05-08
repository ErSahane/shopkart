import random
from io import BytesIO

from django.core.mail import send_mail
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from twilio.rest import Client
from django.conf import settings

from .models import EmailOTP


def create_and_send_otp(user):
    code = f'{random.randint(100000, 999999)}'
    otp, _ = EmailOTP.objects.update_or_create(
        user=user,
        defaults={'code': code, 'expires_at': timezone.now() + timezone.timedelta(minutes=10), 'is_verified': False},
    )
    send_mail(
        'Verify your ShopKart email',
        f'Your ShopKart verification code is {otp.code}. It expires in 10 minutes.',
        None,
        [user.email],
        fail_silently=True,
    )
    return otp


def send_order_confirmation(order):
    send_mail(
        f'ShopKart order {order.order_number} confirmed',
        f'Thank you for shopping with ShopKart. Your order total is Rs. {order.total}.',
        None,
        [order.user.email],
        fail_silently=True,
    )


def generate_invoice_pdf(order):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [
        Paragraph('ShopKart Invoice', styles['Title']),
        Paragraph(f'Order: {order.order_number}', styles['Normal']),
        Paragraph(f'Date: {order.created_at:%d %b %Y}', styles['Normal']),
        Paragraph(f'Customer: {order.user.get_full_name() or order.user.username}', styles['Normal']),
        Spacer(1, 18),
    ]
    rows = [['Product', 'Qty', 'Price', 'Total']]
    for item in order.items.all():
        rows.append([item.product_name, item.quantity, f'Rs. {item.price}', f'Rs. {item.line_total}'])
    rows.extend([
        ['', '', 'Subtotal', f'Rs. {order.subtotal}'],
        ['', '', 'Discount', f'Rs. {order.discount}'],
        ['', '', 'Shipping', f'Rs. {order.shipping_fee}'],
        ['', '', 'Grand Total', f'Rs. {order.total}'],
    ])
    table = Table(rows, colWidths=[260, 60, 90, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111827')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
    ]))
    story.append(table)
    story.append(Spacer(1, 18))
    story.append(Paragraph('Paid via ' + order.get_payment_method_display(), styles['Normal']))
    doc.build(story)
    buffer.seek(0)
    return buffer


def send_whatsapp_order(order):

    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    body = f"""
🛒 NEW ORDER

Order: {order.order_number}

Customer: {order.user.username}

Total: ₹{order.total}

Payment: {order.payment_method}

Address:
{order.address.line1}
{order.address.city}
{order.address.state}

"""

    client.messages.create(
        body=body,
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=settings.YOUR_WHATSAPP_NUMBER
    )