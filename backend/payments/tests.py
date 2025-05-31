from django.test import TestCase, override_settings
from django.conf import settings
import ipaddress # Не используется напрямую в тестах, но нужен для работы is_valid_yookassa_ip
from unittest.mock import patch, MagicMock # MagicMock пока не используется, но пригодится для email
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from .yookassa_handlers import is_valid_yookassa_ip
from .emails import send_payment_success_email_to_user, send_payment_cancelled_email_to_user
from orders.models import Order, OrderItem # Предполагаем, что модели Order и OrderItem доступны
from products.models import Product, Category # <--- Добавленный импорт
# Если у вас User модель кастомная, get_user_model() - правильный путь
User = get_user_model()

# Create your tests here.

# Пример доверенных IP-адресов для тестов (может отличаться от вашего settings.py)
# Важно, чтобы этот список был консистентен с тем, что ожидается в тестах.
TEST_YOOKASSA_TRUSTED_IP_NETWORKS_FOR_TESTS = [
    '185.71.76.0/27', # Реальная сеть из вашего списка
    '77.75.153.0/25',  # Еще одна реальная сеть
    # Не добавляем сюда приватные сети типа 10.0.0.1/32, так как их поведение 
    # при DEBUG=False должно быть False вне зависимости от этого списка.
]

class TestYooKassaIPValidation(TestCase):

    @override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=TEST_YOOKASSA_TRUSTED_IP_NETWORKS_FOR_TESTS, DEBUG=False)
    def test_trusted_public_ip_allowed(self):
        """Проверяет, что публичный IP из доверенного списка разрешен."""
        self.assertTrue(is_valid_yookassa_ip('185.71.76.1'))
        self.assertTrue(is_valid_yookassa_ip('77.75.153.10'))

    @override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=TEST_YOOKASSA_TRUSTED_IP_NETWORKS_FOR_TESTS, DEBUG=False)
    def test_untrusted_public_ip_denied(self):
        """Проверяет, что публичный IP не из доверенного списка запрещен."""
        self.assertFalse(is_valid_yookassa_ip('1.2.3.4'))

    @override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=TEST_YOOKASSA_TRUSTED_IP_NETWORKS_FOR_TESTS, DEBUG=True)
    def test_private_ip_allowed_in_debug(self):
        """Проверяет, что приватные/локальные IP разрешены в режиме DEBUG=True."""
        self.assertTrue(is_valid_yookassa_ip('192.168.1.1')) # Типичный приватный IP
        self.assertTrue(is_valid_yookassa_ip('10.0.0.1'))     # Другой приватный IP
        self.assertTrue(is_valid_yookassa_ip('127.0.0.1'))    # Loopback

    @override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=TEST_YOOKASSA_TRUSTED_IP_NETWORKS_FOR_TESTS, DEBUG=False)
    def test_private_ip_denied_not_in_debug(self):
        """Проверяет, что приватные/локальные IP запрещены, если DEBUG=False."""
        self.assertFalse(is_valid_yookassa_ip('192.168.1.1'))
        self.assertFalse(is_valid_yookassa_ip('10.0.0.1'))
        self.assertFalse(is_valid_yookassa_ip('127.0.0.1'))

    @override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=TEST_YOOKASSA_TRUSTED_IP_NETWORKS_FOR_TESTS, DEBUG=False)
    def test_trusted_private_ip_denied_not_in_debug_if_actually_private(self):
        """Даже если приватная сеть случайно оказалась в списке доверенных, она должна быть отклонена при DEBUG=False."""
        # Создадим список, где приватная сеть ЕСТЬ
        custom_trusted_list = TEST_YOOKASSA_TRUSTED_IP_NETWORKS_FOR_TESTS + ['192.168.1.0/24']
        with override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=custom_trusted_list, DEBUG=False):
            self.assertFalse(is_valid_yookassa_ip('192.168.1.50'))

    @override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=TEST_YOOKASSA_TRUSTED_IP_NETWORKS_FOR_TESTS)
    def test_invalid_ip_string_format(self):
        """Проверяет поведение при передаче некорректной строки IP."""
        self.assertFalse(is_valid_yookassa_ip('invalid-ip-string'))
        self.assertFalse(is_valid_yookassa_ip('256.0.0.1')) # Невалидный октет
        self.assertFalse(is_valid_yookassa_ip('123.0.0')) # Неполный IP

    @override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=TEST_YOOKASSA_TRUSTED_IP_NETWORKS_FOR_TESTS)
    def test_empty_ip_string(self):
        """Проверяет поведение при передаче пустой строки IP."""
        self.assertFalse(is_valid_yookassa_ip(''))

    @override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=None, DEBUG=False)
    def test_no_trusted_networks_configured(self):
        """Проверяет поведение, если YOOKASSA_TRUSTED_IP_NETWORKS не задан (None)."""
        # В этом случае функция должна корректно работать и не падать,
        # возвращая False для любого IP (кроме случая DEBUG=True и приватных IP)
        self.assertFalse(is_valid_yookassa_ip('185.71.76.1'))
        self.assertFalse(is_valid_yookassa_ip('1.2.3.4'))

    @override_settings(YOOKASSA_TRUSTED_IP_NETWORKS=[], DEBUG=False)
    def test_empty_trusted_networks_list(self):
        """Проверяет поведение, если YOOKASSA_TRUSTED_IP_NETWORKS - пустой список."""
        self.assertFalse(is_valid_yookassa_ip('185.71.76.1'))
        self.assertFalse(is_valid_yookassa_ip('1.2.3.4'))

# Дальше будут тесты для email функций

class BaseEmailTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser_email', # Изменено для уникальности, если тесты запускаются вместе 
            email='test@example.com', 
            first_name='Test', 
            password='password'
        )
        
        # Создадим категорию и продукт для OrderItem
        self.category = Category.objects.create(name='Test Email Category', slug='test-email-category-payments')
        self.product = Product.objects.create(
            name='Test Email Product for Payments',
            slug='test-email-product-payments',
            category=self.category,
            price=Decimal('123.45'), # Конкретная цена для проверки
            stock=10,
            available=True
        )

        self.order = Order.objects.create(
            user=self.user,
            address='123 Test St',
            status='pending',
            paid=False,
            # id=123 # Убрал фиксированный ID, чтобы избежать конфликтов при параллельном запуске или повторах
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product, # Связываем с продуктом
            price=self.product.price, # Используем цену продукта
            quantity=1
        )
        # self.order.get_total_cost теперь должен работать корректно

@override_settings(
    SITE_URL='http://testserver',
    SITE_DOMAIN='testserver.com',
    DEFAULT_FROM_EMAIL='noreply@testserver.com',
    EMAIL_SUBJECT_PREFIX='[TestSite] '
)
class TestSendPaymentSuccessEmail(BaseEmailTest):

    def setUp(self):
        super().setUp()
        self.order.paid = True
        self.order.paid_at = timezone.now()
        self.order.status = 'processing'
        self.order.save()

    @patch('payments.emails.EmailMultiAlternatives')
    @patch('payments.emails.render_to_string')
    def test_send_payment_success_email_to_user(self, mock_render_to_string, mock_email_multi_alternatives):
        # Настроим моки render_to_string
        # Первый вызов для subject, второй для html_body, третий для text_body
        mock_render_to_string.side_effect = [
            'Test Subject Success',  # subject
            '<html>Test HTML Body Success</html>',  # html_body
            'Test Text Body Success'  # text_body
        ]
        mock_send = MagicMock()
        mock_email_multi_alternatives.return_value.send = mock_send

        send_payment_success_email_to_user(self.order)

        self.assertEqual(mock_render_to_string.call_count, 3)
        # Проверка вызова для subject
        mock_render_to_string.assert_any_call(
            'payments/email/payment_success_user_subject.txt', 
            {
                'order': self.order,
                'user_greeting_name': self.user.first_name,
                'order_total_cost': self.order.get_total_cost(),
                'order_paid_at_formatted': self.order.paid_at.strftime('%d.%m.%Y в %H:%M:%S %Z'),
                'order_items': list(self.order.items.all()),
                'site_url': 'http://testserver',
                'site_domain': 'testserver.com',
            }
        )
        # Проверка вызова для html_body
        mock_render_to_string.assert_any_call(
            'payments/email/payment_success_user_body.html',
            # context такой же
            {
                'order': self.order,
                'user_greeting_name': self.user.first_name,
                'order_total_cost': self.order.get_total_cost(),
                'order_paid_at_formatted': self.order.paid_at.strftime('%d.%m.%Y в %H:%M:%S %Z'),
                'order_items': list(self.order.items.all()),
                'site_url': 'http://testserver',
                'site_domain': 'testserver.com',
            }
        )
        # Проверка вызова для text_body
        mock_render_to_string.assert_any_call(
            'payments/email/payment_success_user_body.txt',
            # context такой же
            {
                'order': self.order,
                'user_greeting_name': self.user.first_name,
                'order_total_cost': self.order.get_total_cost(),
                'order_paid_at_formatted': self.order.paid_at.strftime('%d.%m.%Y в %H:%M:%S %Z'),
                'order_items': list(self.order.items.all()),
                'site_url': 'http://testserver',
                'site_domain': 'testserver.com',
            }
        )
        
        expected_subject = settings.EMAIL_SUBJECT_PREFIX + 'Test Subject Success'
        mock_email_multi_alternatives.assert_called_once_with(
            expected_subject,
            'Test Text Body Success', # text_body
            'noreply@testserver.com', # from_email
            [self.user.email] # recipient_list
        )
        mock_email_multi_alternatives.return_value.attach_alternative.assert_called_once_with(
            '<html>Test HTML Body Success</html>', "text/html"
        )
        mock_send.assert_called_once()

    @patch('payments.emails.EmailMultiAlternatives')
    @patch('payments.emails.logger')
    def test_send_payment_success_email_no_user_email(self, mock_logger, mock_email_multi_alternatives):
        self.order.user.email = ''
        self.order.user.save()
        
        send_payment_success_email_to_user(self.order)
        
        mock_email_multi_alternatives.assert_not_called()
        mock_logger.warning.assert_called_once()
        self.assertIn(f"Не удалось отправить письмо об успехе для заказа ID {self.order.id}", mock_logger.warning.call_args[0][0])

@override_settings(
    SITE_URL='http://testserver',
    SITE_DOMAIN='testserver.com',
    DEFAULT_FROM_EMAIL='noreply@testserver.com',
    EMAIL_SUBJECT_PREFIX='[TestSite] '
)
class TestSendPaymentCancelledEmail(BaseEmailTest):

    def setUp(self):
        super().setUp()
        self.order.status = 'cancelled'
        self.order.save()

    @patch('payments.emails.EmailMultiAlternatives')
    @patch('payments.emails.render_to_string')
    def test_send_payment_cancelled_email_to_user(self, mock_render_to_string, mock_email_multi_alternatives):
        mock_render_to_string.side_effect = [
            'Test Subject Cancelled',
            '<html>Test HTML Body Cancelled</html>',
            'Test Text Body Cancelled'
        ]
        mock_send = MagicMock()
        mock_email_multi_alternatives.return_value.send = mock_send
        cancellation_reason = "Недостаточно средств"

        send_payment_cancelled_email_to_user(self.order, cancellation_reason)

        self.assertEqual(mock_render_to_string.call_count, 3)
        expected_context = {
            'order': self.order,
            'user_greeting_name': self.user.first_name,
            'order_total_cost': self.order.get_total_cost(),
            'cancellation_reason': cancellation_reason,
            'site_url': 'http://testserver',
            'site_domain': 'testserver.com',
        }
        mock_render_to_string.assert_any_call('payments/email/payment_cancelled_user_subject.txt', expected_context)
        mock_render_to_string.assert_any_call('payments/email/payment_cancelled_user_body.html', expected_context)
        mock_render_to_string.assert_any_call('payments/email/payment_cancelled_user_body.txt', expected_context)
        
        expected_subject = settings.EMAIL_SUBJECT_PREFIX + 'Test Subject Cancelled'
        mock_email_multi_alternatives.assert_called_once_with(
            expected_subject,
            'Test Text Body Cancelled',
            'noreply@testserver.com',
            [self.user.email]
        )
        mock_email_multi_alternatives.return_value.attach_alternative.assert_called_once_with(
            '<html>Test HTML Body Cancelled</html>', "text/html"
        )
        mock_send.assert_called_once()

    @patch('payments.emails.EmailMultiAlternatives')
    @patch('payments.emails.logger')
    def test_send_payment_cancelled_email_no_user_email(self, mock_logger, mock_email_multi_alternatives):
        self.order.user.email = ''
        self.order.user.save()
        
        send_payment_cancelled_email_to_user(self.order, "Причина не важна")
        
        mock_email_multi_alternatives.assert_not_called()
        mock_logger.warning.assert_called_once()
        self.assertIn(f"Не удалось отправить письмо об отмене платежа для заказа ID {self.order.id}", mock_logger.warning.call_args[0][0])
