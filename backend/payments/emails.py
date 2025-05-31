import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Предполагается, что у вас есть модель Order, импортируйте ее правильно
# from orders.models import Order 
# Однако, чтобы избежать циклического импорта, лучше передавать объект order,
# а не импортировать Order здесь, если emails.py используется только из handlers.py
# Если emails.py будет импортироваться еще откуда-то, где Order уже есть, то можно.
# Для простоты пока оставим так, но в реальном проекте тип order лучше аннотировать:
# from orders.models import Order (для type hinting, если не вызывает циклов)

logger = logging.getLogger(__name__)

def send_payment_success_email_to_user(order):
    """Отправляет email-уведомление пользователю об успешной оплате заказа с использованием шаблонов."""
    if not hasattr(order, 'user') or not order.user or not hasattr(order.user, 'email') or not order.user.email:
        logger.warning(f"[Email Уведомление] Не удалось отправить письмо об успехе для заказа ID {getattr(order, 'id', 'N/A')}: email пользователя не найден или структура заказа некорректна.")
        return

    user_greeting_name = getattr(order.user, 'first_name', None) or order.user.email
    order_total_cost = order.get_total_cost()
    order_paid_at_formatted = order.paid_at.strftime('%d.%m.%Y в %H:%M:%S %Z') if order.paid_at else 'не указана'
    order_items = list(order.items.all()) # Получаем связанные товары/услуги

    # Используем SITE_URL и SITE_DOMAIN из настроек Django
    site_url = settings.SITE_URL
    site_domain = settings.SITE_DOMAIN

    context = {
        'order': order,
        'user_greeting_name': user_greeting_name,
        'order_total_cost': order_total_cost,
        'order_paid_at_formatted': order_paid_at_formatted,
        'order_items': order_items,
        'site_url': site_url,
        'site_domain': site_domain,
    }

    try:
        subject_template = 'payments/email/payment_success_user_subject.txt'
        html_body_template = 'payments/email/payment_success_user_body.html'
        text_body_template = 'payments/email/payment_success_user_body.txt'

        subject = render_to_string(subject_template, context).strip()
        # Если EMAIL_SUBJECT_PREFIX должен применяться ко всем темам, его можно добавить здесь:
        # subject = f"{settings.EMAIL_SUBJECT_PREFIX}{subject}"
        # Однако, если он уже в settings.EMAIL_SUBJECT_PREFIX, и шаблон темы НЕ должен его дублировать,
        # то либо убираем его из settings.EMAIL_SUBJECT_PREFIX, либо проверяем перед добавлением.
        # Для простоты, предполагаем, что settings.EMAIL_SUBJECT_PREFIX управляет этим глобально, и шаблон темы его не включает.
        # Если settings.EMAIL_SUBJECT_PREFIX пуст, то тема будет как в шаблоне.
        if settings.EMAIL_SUBJECT_PREFIX and not subject.startswith(settings.EMAIL_SUBJECT_PREFIX.strip()):
             subject = f"{settings.EMAIL_SUBJECT_PREFIX.strip()} {subject}" # Добавляем, если его нет
        elif not settings.EMAIL_SUBJECT_PREFIX: # Если префикс пуст в настройках, тема берется чистой из шаблона
            pass # subject уже содержит значение из шаблона

        html_body = render_to_string(html_body_template, context)
        text_body = render_to_string(text_body_template, context)
        
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [order.user.email]

        msg = EmailMultiAlternatives(subject, text_body, from_email, recipient_list)
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        logger.info(f"[Email Уведомление] Письмо (HTML+Text) об успешной оплате заказа {order.id} отправлено пользователю {order.user.email}.")
    except Exception as e:
        logger.exception(f"[Email Уведомление] Ошибка при отправке письма (HTML+Text) об оплате заказа {order.id} пользователю {order.user.email}: {e}")

def send_payment_cancelled_email_to_user(order, cancellation_reason="не указана"):
    """Отправляет email-уведомление пользователю об отмене платежа по заказу."""
    if not hasattr(order, 'user') or not order.user or not hasattr(order.user, 'email') or not order.user.email:
        logger.warning(f"[Email Уведомление] Не удалось отправить письмо об отмене платежа для заказа ID {getattr(order, 'id', 'N/A')}: email пользователя не найден.")
        return

    user_greeting_name = getattr(order.user, 'first_name', None) or order.user.email
    order_total_cost = order.get_total_cost()

    site_url = settings.SITE_URL
    site_domain = settings.SITE_DOMAIN

    context = {
        'order': order,
        'user_greeting_name': user_greeting_name,
        'order_total_cost': order_total_cost,
        'cancellation_reason': cancellation_reason,
        'site_url': site_url,
        'site_domain': site_domain,
    }

    try:
        subject_template = 'payments/email/payment_cancelled_user_subject.txt'
        html_body_template = 'payments/email/payment_cancelled_user_body.html'
        text_body_template = 'payments/email/payment_cancelled_user_body.txt'

        subject = render_to_string(subject_template, context).strip()
        if settings.EMAIL_SUBJECT_PREFIX and not subject.startswith(settings.EMAIL_SUBJECT_PREFIX.strip()):
            subject = f"{settings.EMAIL_SUBJECT_PREFIX.strip()} {subject}"
        
        html_body = render_to_string(html_body_template, context)
        text_body = render_to_string(text_body_template, context)
        
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [order.user.email]

        msg = EmailMultiAlternatives(subject, text_body, from_email, recipient_list)
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        logger.info(f"[Email Уведомление] Письмо (HTML+Text) об ОТМЕНЕ платежа по заказу {order.id} отправлено пользователю {order.user.email}.")
    except Exception as e:
        logger.exception(f"[Email Уведомление] Ошибка при отправке письма (HTML+Text) об ОТМЕНЕ платежа по заказу {order.id} пользователю {order.user.email}: {e}") 