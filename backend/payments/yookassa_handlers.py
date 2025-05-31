from django.http import JsonResponse, HttpResponse, HttpRequest
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings # Для доступа к YOOKASSA_SHOP_ID indirectly
from django.utils import timezone # Для фиксации времени оплаты
from django.core.mail import mail_admins # send_mail убран отсюда, он теперь в emails.py
from django.template.loader import render_to_string # Для использования шаблонов в письмах (пока не используется)
import uuid
import logging
import json # Для парсинга вебхука, если понадобится ручная обработка
import ipaddress # <--- Добавлен импорт
# from urllib.parse import urlparse # Больше не нужно здесь

# Импорты для ЮKassa
from yookassa import Configuration, Payment
from yookassa.domain.models.currency import Currency
from yookassa.domain.request.payment_request_builder import PaymentRequestBuilder
from yookassa.domain.notification import WebhookNotification # Убедимся, что правильный класс импортирован
from yookassa.domain.exceptions import ApiError, BadRequestError, ForbiddenError, NotFoundError, TooManyRequestsError, UnauthorizedError
from orders.models import Order # <--- Добавленный импорт
from cart.models import Cart # <--- Добавленный импорт
from .emails import send_payment_success_email_to_user, send_payment_cancelled_email_to_user # <--- Новый импорт

# Импорты для DRF APIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status as drf_status # Для использования стандартных HTTP статусов DRF
# Предполагаемый импорт для JWTAuthentication, если используется simplejwt
# Если используется dj_rest_auth, он может предоставлять свой класс или настраивать simplejwt.
# Убедитесь, что этот класс доступен и правильно настроен в settings.py
from rest_framework_simplejwt.authentication import JWTAuthentication 

# Логгер
logger = logging.getLogger(__name__)

# --- Вспомогательная функция для проверки конфигурации ЮKassa ---
def is_yookassa_configured():
    """Проверяет, заданы ли ID магазина и секретный ключ ЮKassa."""
    # Доступ к Configuration.account_id и Configuration.secret_key происходит после Configuration.configure()
    # который вызывается в settings.py. Если ключи не были заданы в .env, они будут None.
    return bool(Configuration.account_id and Configuration.secret_key)

# --- Вспомогательная функция для проверки IP-адреса ЮKassa --- 
def is_valid_yookassa_ip(client_ip_str: str) -> bool:
    """Проверяет, принадлежит ли IP-адрес клиента одной из доверенных сетей YooKassa."""
    # ВРЕМЕННО ДЛЯ ОТЛАДКИ: Если DEBUG=True, считаем любой IP валидным, чтобы проверить остальную логику
    # if settings.DEBUG:
    #     logger.warning(f"[YooKassa Webhook IP Check - DEBUG MODE] Проверка IP отключена (settings.DEBUG is True). IP клиента: {client_ip_str}")
    #     return True

    if not client_ip_str:
        logger.warning("[YooKassa Webhook IP Check] IP-адрес клиента не определен.")
        return False
    try:
        client_ip = ipaddress.ip_address(client_ip_str)
        if client_ip.is_loopback or client_ip.is_private:
            if settings.DEBUG:
                logger.warning(f"[YooKassa Webhook IP Check] РАЗРЕШЕН ЛОКАЛЬНЫЙ/ПРИВАТНЫЙ IP: {client_ip_str} (settings.DEBUG is True). В production DEBUG должен быть False.")
                return True
            else:
                logger.warning(f"[YooKassa Webhook IP Check] Отклонен локальный/приватный IP: {client_ip_str} (settings.DEBUG is False).")
                return False

        trusted_networks = getattr(settings, 'YOOKASSA_TRUSTED_IP_NETWORKS', None)
        if not trusted_networks: # Если None или пустой список
            logger.warning(f"[YooKassa Webhook IP Check] Список YOOKASSA_TRUSTED_IP_NETWORKS не настроен или пуст. IP {client_ip_str} считается НЕДОВЕРЕННЫМ.")
            return False

        for trusted_network_str in trusted_networks:
            try:
                trusted_network = ipaddress.ip_network(trusted_network_str, strict=False)
                if client_ip in trusted_network:
                    logger.debug(f"[YooKassa Webhook IP Check] IP {client_ip_str} принадлежит доверенной сети {trusted_network_str}.")
                    return True
            except ValueError as e_net:
                logger.error(f"[YooKassa Webhook IP Check] Ошибка при парсинге доверенной сети '{trusted_network_str}' из settings: {e_net}")
                continue # Пропускаем невалидную сеть и проверяем следующие
        
        logger.warning(f"[YooKassa Webhook IP Check] IP {client_ip_str} НЕ принадлежит ни одной из доверенных сетей YooKassa.")
        return False
    except ValueError as e_ip:
        logger.error(f"[YooKassa Webhook IP Check] Ошибка при парсинге IP-адреса клиента '{client_ip_str}': {e_ip}")
        return False

# --- Views --- 

# @csrf_exempt # <--- Убираем декоратор, APIView сама управляет CSRF (обычно не нужен для API с токенами)
# def create_yookassa_payment_view(request: HttpRequest, order_id: int): <-- Старая сигнатура

class CreateYookassaPaymentView(APIView):
    """
    Создает платеж в ЮKassa для указанного order_id.
    Вызывается с фронтенда, требует аутентификации пользователя.
    """
    authentication_classes = [JWTAuthentication] # <--- ПРАВИЛЬНО (если используется simplejwt)
    permission_classes = [IsAuthenticated]     # <--- ПРАВИЛЬНО

    def post(self, request: HttpRequest, order_id: int): # Метод POST, как и был
        # request.user теперь должен быть корректно установлен благодаря DRF и IsAuthenticated
        logger.info(f"[YooKassa] Запрос на создание платежа для заказа ID: {order_id} от пользователя {request.user.email if hasattr(request.user, 'email') else request.user.id}")

        if not is_yookassa_configured():
            logger.error("[YooKassa] SDK не сконфигурирован. Проверьте YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env файле.")
            # Используем Response от DRF
            return Response({"status": "error", "message": "Сервис оплаты временно недоступен. Пожалуйста, повторите попытку позже."}, status=drf_status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            # --- 1. Получить детали вашего заказа из БД ---
            try:
                # request.user теперь должен быть аутентифицированным пользователем
                order = Order.objects.get(id=order_id, user=request.user) 
            except Order.DoesNotExist:
                logger.warning(f"[YooKassa] Заказ ID: {order_id} не найден или не принадлежит пользователю {request.user.id}.")
                return Response({"status": "error", "message": "Заказ не найден."}, status=drf_status.HTTP_404_NOT_FOUND)

            # --- 2. Проверить, что заказ еще не оплачен и может быть оплачен ---
            if order.paid:
                logger.info(f"[YooKassa] Заказ ID: {order_id} уже был успешно оплачен.")
                return Response({"status": "info", "message": "Этот заказ уже оплачен."}, status=drf_status.HTTP_200_OK) 

            if order.status == 'cancelled':
                 logger.warning(f"[YooKassa] Попытка оплатить отмененный заказ ID: {order_id}.")
                 return Response({"status": "error", "message": "Этот заказ отменен и не может быть оплачен."}, status=drf_status.HTTP_400_BAD_REQUEST)
            
            order_amount = order.get_total_cost()
            order_description = f"Оплата заказа №{order.id} в интернет-магазине 'BAT3D Store'"
            
            idempotence_key = str(uuid.uuid4())
            
            # Формируем URL для возврата на фронтенд
            # settings.SITE_URL должен указывать на базовый URL вашего фронтенда (например, http://localhost:3000)
            # Мы добавим к нему путь к странице успеха и параметры
            # Если SITE_URL не настроен или указывает на бэкенд, это нужно будет исправить в settings.py
            frontend_success_url = f"{settings.SITE_URL}/order/success"
            return_url_for_yookassa = f"{frontend_success_url}?orderId={order_id}&yookassa_payment=true"
            
            logger.info(f"[YooKassa] Return URL для заказа {order_id} будет: {return_url_for_yookassa}")

            builder = PaymentRequestBuilder()
            builder.set_amount({"value": f"{order_amount:.2f}", "currency": Currency.RUB})
            builder.set_capture(True)
            builder.set_confirmation({"type": "redirect", "return_url": return_url_for_yookassa})
            builder.set_description(order_description)
            builder.set_metadata({"internal_order_id": str(order_id)})
            payment_request_payload = builder.build()

            logger.debug(f"[YooKassa] Payload для создания платежа (Order ID: {order_id}): {payment_request_payload}")
            payment_response = Payment.create(payment_request_payload, idempotence_key)
            confirmation_url = payment_response.confirmation.confirmation_url

            order.yookassa_payment_id = payment_response.id
            update_fields_list = ['yookassa_payment_id']
            if order.status != 'pending':
                order.status = 'pending'
                update_fields_list.append('status')
                logger.info(f"[YooKassa] Статус заказа {order.id} изменен на 'pending' перед ожиданием оплаты ЮKassa.")
            order.save(update_fields=update_fields_list)

            logger.info(f"[YooKassa] Платеж успешно создан. YooKassa Payment ID: {payment_response.id} для Order ID: {order.id}. URL для оплаты: {confirmation_url}")
            return Response({"status": "success", "payment_url": confirmation_url, "yookassa_payment_id": payment_response.id}, status=drf_status.HTTP_200_OK)

        except (BadRequestError, ForbiddenError, UnauthorizedError) as e_user:
            logger.error(f"[YooKassa] Клиентская ошибка API при создании платежа для заказа {order_id}: {e_user}. Response: {e_user.response_body if hasattr(e_user, 'response_body') else 'N/A'}")
            return Response({"status": "error", "message": "Ошибка при инициации платежа. Пожалуйста, проверьте введенные данные или попробуйте позже."}, status=drf_status.HTTP_400_BAD_REQUEST)
        except (ApiError, TooManyRequestsError, NotFoundError) as e_server:
            logger.error(f"[YooKassa] Серверная ошибка API при создании платежа для заказа {order_id}: {e_server}. Response: {e_server.response_body if hasattr(e_server, 'response_body') else 'N/A'}")
            return Response({"status": "error", "message": "Внутренняя ошибка сервиса оплаты. Пожалуйста, попробуйте оплатить заказ позже."}, status=drf_status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.exception(f"[YooKassa] Непредвиденная ошибка при создании платежа для заказа {order_id}: {e}")
            return Response({"status": "error", "message": "Произошла системная ошибка при попытке создать платеж."}, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)

# yookassa_return_url_view остается функцией, так как она не требует строгой DRF аутентификации (пользователь просто перенаправляется)
# Но ее можно будет тоже переделать в APIView без IsAuthenticated, если захочется единообразия
@csrf_exempt # Для return URL можно оставить csrf_exempt, если он не обрабатывает POST с конфиденциальными данными
def yookassa_return_url_view(request: HttpRequest, order_id: int):
    """
    Обрабатывает возвращение пользователя на сайт после взаимодействия со страницей оплаты ЮKassa.
    Эта view НЕ должна изменять статус заказа на "оплачен". Это задача вебхука.
    Задача этой view - проинформировать пользователя и, возможно, инициировать проверку статуса.
    """
    logger.info(f"[YooKassa] Пользователь вернулся на сайт для заказа ID: {order_id}. GET параметры: {request.GET.urlencode()}")

    order = None
    yookassa_status = None # Статус от ЮKassa, если удалось получить
    message = "Спасибо! Ваш платеж обрабатывается ЮKassa. Вы получите уведомление о результате на указанную почту или в личном кабинете." # Сообщение по умолчанию
    page_title = "Статус платежа"

    try:
        # Ищем заказ только по order_id. 
        # Проверку принадлежности пользователю здесь убираем, т.к. request.user может быть AnonymousUser
        # Эта view только отображает информацию.
        order = Order.objects.get(id=order_id) 
    except Order.DoesNotExist:
        logger.warning(f"[YooKassa Return URL] Заказ ID: {order_id} не найден.")
        context_error = {
            'order_id': order_id,
            'page_title': "Ошибка платежа",
            'message': "К сожалению, указанный заказ не найден. Пожалуйста, проверьте правильность ссылки или обратитесь в поддержку."
        }
        return render(request, 'payments/payment_status_page.html', context_error, status=404)

    # Пытаемся получить текущий статус платежа из ЮKassa, если есть ID
    if order.yookassa_payment_id and is_yookassa_configured():
        try:
            payment_info = Payment.find_one(order.yookassa_payment_id)
            yookassa_status = payment_info.status # 'pending', 'waiting_for_capture', 'succeeded', 'canceled'
            logger.info(f"[YooKassa Return URL] Проверка статуса для YK Payment ID {order.yookassa_payment_id} (Order ID: {order.id}): {yookassa_status}")
            
            if yookassa_status == 'succeeded':
                page_title = "Платеж успешно выполнен"
                message = "Ваш платеж успешно получен! Заказ скоро будет обработан."
            elif yookassa_status == 'canceled':
                page_title = "Платеж отменен"
                message = "Платеж был отменен. Вы можете попробовать оплатить заказ снова из вашего личного кабинета."
            elif yookassa_status == 'pending' or yookassa_status == 'waiting_for_capture':
                page_title = "Платеж в обработке"
                message = "Ваш платеж ожидает подтверждения от ЮKassa. Обычно это занимает несколько секунд."

        except ApiError as e:
            logger.error(f"[YooKassa Return URL] Ошибка API ЮKassa при проверке статуса платежа {order.yookassa_payment_id} для заказа {order.id}: {e}")
        except Exception as e:
            logger.error(f"[YooKassa Return URL] Непредвиденная ошибка при проверке статуса платежа {order.yookassa_payment_id} для заказа {order.id}: {e}")

    context = {
        'order_id': order_id,
        'order': order,
        'page_title': page_title,
        'message': message,
        'yookassa_status': yookassa_status,
        'yookassa_query_params': dict(request.GET)
    }
    
    return render(request, 'payments/payment_status_page.html', context)

@csrf_exempt
def yookassa_webhook_view(request: HttpRequest):
    # Получаем IP до любых проверок для логирования
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        client_ip_for_log = x_forwarded_for.split(',')[0].strip()
    else:
        client_ip_for_log = request.META.get('REMOTE_ADDR')
    logger.info(f"[YooKassa Webhook ATTEMPT] Path: {request.path}, Method: {request.method}, IP: {client_ip_for_log}") # <--- Новый лог

    logger.info(f"!!!!!!!!!!!!!! [YooKassa Webhook RECEIVED] !!!!!!!!!!!!!!") # Очень заметный лог
    logger.info(f"[YooKassa Webhook DEBUG] Method: {request.method}, Path: {request.path}")
    logger.info(f"[YooKassa Webhook DEBUG] Headers: {dict(request.headers)}")
    if request.method == 'POST':
        raw_body = request.body.decode('utf-8', errors='ignore')
        logger.info(f"[YooKassa Webhook DEBUG] Raw Body: {raw_body}")
    # --- (ВАЖНО ДЛЯ БЕЗОПАСНОСТИ) Проверка IP-адреса источника запроса. ---
    # Список IP-адресов ЮKassa: https://yookassa.ru/docs/support/technical-faq/notifications
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Если есть X-Forwarded-For, берем самый левый IP (обычно это исходный IP клиента)
        client_ip = x_forwarded_for.split(',')[0].strip()
    else:
        client_ip = request.META.get('REMOTE_ADDR')

    if not is_valid_yookassa_ip(client_ip):
        logger.warning(f"[YooKassa Webhook] Вебхук от НЕДОВЕРЕННОГО IP: {client_ip}. Тело (первые 256б): {request.body[:256].decode('utf-8', errors='ignore')}")
        return HttpResponse(status=403) # Forbidden
    
    logger.debug(f"[YooKassa Webhook] Вебхук от доверенного IP: {client_ip}")
    # --- Конец проверки IP-адреса ---

    if request.method == 'POST':
        try:
            event_body = request.body.decode('utf-8')
            event_json = json.loads(event_body)
            logger.info(f"[YooKassa] Получен вебхук: Event: {event_json.get('event')}, Object ID: {event_json.get('object', {}).get('id')}")
            # logger.debug(f"[YooKassa] Полное тело вебхука: {event_body}")
            
            # Валидация и парсинг уведомления с помощью SDK
            notification_object = WebhookNotification(event_json)
            payment_data = notification_object.object # Это объект Payment или Refund

            # Убедимся, что это уведомление о платеже, а не о возврате
            # Проверяем тип события вместо несуществующего атрибута .type у payment_data
            current_event_type = event_json.get('event', '')
            if not current_event_type.startswith("payment."):
                 logger.info(f"[YooKassa] Вебхук для события '{current_event_type}' (Объект ID: {payment_data.id}). Пропускаем, так как ожидается событие 'payment.*'.")
                 return HttpResponse(status=200) # Отвечаем ОК, чтобы ЮKassa не повторяла

            # Получаем метаданные, если они были переданы при создании платежа
            metadata = payment_data.metadata
            internal_order_id = metadata.get('internal_order_id') if metadata else None
            yk_payment_id = payment_data.id

            logger.info(f"[YooKassa] Обработка вебхука для платежа: YooKassa Payment ID: {yk_payment_id}, Internal Order ID (из metadata): {internal_order_id}, Статус ЮKassa: {payment_data.status}")

            # --- Поиск вашего внутреннего заказа --- 
            order = None
            if yk_payment_id: # Предпочтительный способ поиска
                try:
                    order = Order.objects.get(yookassa_payment_id=yk_payment_id)
                except Order.DoesNotExist:
                    # Если не нашли по yk_payment_id, и есть internal_order_id из метаданных, 
                    # можно попробовать найти заказ, у которого yk_payment_id еще не установлен.
                    # Это может быть полезно, если по какой-то причине yookassa_payment_id не успел сохраниться до вебхука,
                    # или если вебхук пришел раньше, чем ответ в create_yookassa_payment_view (маловероятно, но возможно).
                    if internal_order_id:
                        try:
                            order = Order.objects.get(id=internal_order_id, yookassa_payment_id__isnull=True)
                            logger.info(f"[YooKassa Webhook] Заказ ID {internal_order_id} найден по internal_order_id (YooKassa ID был null). Присваиваем YooKassa Payment ID: {yk_payment_id}")
                            order.yookassa_payment_id = yk_payment_id # Присваиваем ID, если нашли таким образом
                            # Статус здесь не меняем, это произойдет ниже на основе payment_data.status
                        except Order.DoesNotExist:
                            logger.error(f"[YooKassa Webhook] Заказ не найден ни по YooKassa Payment ID {yk_payment_id}, ни по Internal Order ID {internal_order_id} (с yk_id=null).")
                            # Отвечаем 200, чтобы YooKassa не повторяла, т.к. мы не можем обработать этот вебхук.
                            return HttpResponse(status=200) 
            elif internal_order_id: # Если по какой-то причине yk_payment_id не пришел в вебхуке, но есть internal_order_id
                try:
                    # Ищем заказ только по internal_order_id. Это менее надежно.
                    order = Order.objects.get(id=internal_order_id)
                    logger.warning(f"[YooKassa Webhook] Заказ ID {internal_order_id} найден ТОЛЬКО по internal_order_id. YooKassa Payment ID не было в вебхуке (или был пуст).")
                    if not order.yookassa_payment_id: # Если у него еще нет YK ID, присваиваем
                        order.yookassa_payment_id = yk_payment_id
                        logger.info(f"[YooKassa Webhook] Присвоен YooKassa Payment ID {yk_payment_id} заказу {internal_order_id}, найденному по internal_order_id.")
                except Order.DoesNotExist:
                    logger.error(f"[YooKassa Webhook] Заказ не найден по Internal Order ID {internal_order_id} (YooKassa Payment ID также отсутствовал в вебхуке).")
                    return HttpResponse(status=200) # Не можем обработать
            else:
                logger.error(f"[YooKassa Webhook] Невозможно идентифицировать заказ: отсутствует и YooKassa Payment ID в объекте платежа, и internal_order_id в метаданных.")
                return HttpResponse(status=400) # Bad Request - вебхук не содержит достаточно данных
            
            # Если после всех попыток заказ не найден
            if not order:
                logger.error(f"[YooKassa Webhook] КРИТИЧЕСКАЯ ОШИБКА: Заказ не удалось идентифицировать для YooKassa Payment ID: {yk_payment_id} / Internal Order ID: {internal_order_id}. Вебхук не может быть обработан.")
                return HttpResponse(status=200) # Отвечаем 200, чтобы YooKassa не повторяла, но проблема залогирована
            
            # --- Логика обработки статусов платежа --- 
            if payment_data.status == 'succeeded':
                if payment_data.paid:
                    if order.paid:
                        logger.info(f"[YooKassa Webhook] Заказ {order.id} уже был отмечен как оплаченный. Повторный вебхук 'succeeded'.")
                    else:
                        order.paid = True
                        order.paid_at = timezone.now()
                        order.status = 'processing'
                        order.save(update_fields=['paid', 'paid_at', 'status', 'yookassa_payment_id'])
                        logger.info(f"[YooKassa Webhook] УСПЕХ: Заказ {order.id} (YK ID: {yk_payment_id}) обновлен: paid=True, status='processing', paid_at={order.paid_at}")
                        try:
                            send_payment_success_email_to_user(order)
                        except Exception as email_exc:
                            logger.error(f"[YooKassa Webhook] Ошибка при вызове send_payment_success_email_to_user для заказа {order.id}: {email_exc}")
                        
                        # Очистка корзины пользователя после успешной оплаты
                        try:
                            cart = Cart.objects.get(user=order.user)
                            cart.clear_cart() # Предполагается, что у модели Cart есть метод clear_cart()
                            logger.info(f"[YooKassa Webhook] Корзина для пользователя {order.user.id} успешно очищена после оплаты заказа {order.id}.")
                        except Cart.DoesNotExist:
                            logger.warning(f"[YooKassa Webhook] Корзина для пользователя {order.user.id} не найдена. Очистка не требуется.")
                        except Exception as cart_exc:
                            logger.error(f"[YooKassa Webhook] Ошибка при очистке корзины для пользователя {order.user.id} после заказа {order.id}: {cart_exc}")

                        # --- TODO: Дальнейшие действия после успешной оплаты --- 
                        # Здесь может быть ваша бизнес-логика:
                        # 1. Уведомление менеджеров/склада о новом оплаченном заказе (например, по email или через API другой системы).
                        #    Пример: send_new_paid_order_notification_to_managers(order)
                        # 2. Если товары цифровые - предоставление доступа.
                        # 3. Запуск внутренних процессов учета.
                        # 4. Автоматическое изменение статуса на следующий, если это применимо.
                        #    Например, если после 'processing' сразу идет 'awaiting_shipment' без ручного вмешательства:
                        #    if order.status == 'processing': 
                        #        # Тут могут быть доп. проверки, если нужны
                        #        order.status = 'awaiting_shipment'
                        #        order.save(update_fields=['status'])
                        #        logger.info(f"[YooKassa Webhook] Статус заказа {order.id} автоматически изменен на 'awaiting_shipment'.")
                        #        # Можно отправить доп. уведомление пользователю или менеджерам об этом статусе.
                        # logger.info(f"[YooKassa Webhook] Завершены все действия после успешной оплаты заказа {order.id}.")
                        # --- Конец блока TODO ---

                    # TODO: Выполнить другие действия после успешной оплаты (начало сборки заказа и т.д.) <-- Старый TODO, можно удалить или переосмыслить
                else:
                    logger.warning(f"[YooKassa Webhook] Платеж для YooKassa Payment ID: {yk_payment_id} (Order ID: {order.id}) имеет статус 'succeeded', но 'paid' is FALSE. Требуется проверка в ЛК ЮKassa.")
            elif payment_data.status == 'canceled':
                logger.info(f"[YooKassa Webhook] Платеж ОТМЕНЕН для YooKassa Payment ID: {yk_payment_id}, Order ID: {order.id}. Причина: {payment_data.cancellation_details.reason if payment_data.cancellation_details else 'N/A'}")
                # Если заказ еще не был оплачен и не отменен ранее
                if not order.paid and order.status != 'cancelled': 
                    order.status = 'cancelled' # или 'pending' если хотите дать шанс оплатить снова, но тогда надо бы очистить yookassa_payment_id
                    # order.yookassa_payment_id = None # Опционально, если хотите разрешить новую попытку оплаты для ЭТОГО же заказа
                    order.save(update_fields=['status', 'yookassa_payment_id'])
                    logger.info(f"[YooKassa Webhook] Статус заказа {order.id} обновлен на '{order.status}' после отмены платежа ЮKassa.")
                    # Отправляем email пользователю об отмене
                    cancellation_details = payment_data.cancellation_details
                    reason_for_email = cancellation_details.reason if cancellation_details else "не указана"
                    try:
                        send_payment_cancelled_email_to_user(order, cancellation_reason=reason_for_email)
                    except Exception as email_exc:
                        logger.error(f"[YooKassa Webhook] Ошибка при вызове send_payment_cancelled_email_to_user для заказа {order.id}: {email_exc}")
                else:
                    logger.info(f"[YooKassa Webhook] Платеж для заказа {order.id} отменен, но заказ уже был (paid: {order.paid}, status: {order.status}). Дополнительных действий со статусом заказа не требуется.")
            elif payment_data.status == 'waiting_for_capture': # Если вы использовали capture=False при создании платежа
                 logger.info(f"[YooKassa Webhook] Платеж ОЖИДАЕТ ЗАХВАТА для YooKassa Payment ID: {yk_payment_id}, Order ID: {order.id}")
                 # TODO: Если вы используете двухстадийные платежи, здесь логика для решения о захвате.
                 # if should_capture_payment_now(order):
                 #     try:
                 #         capture_idempotence_key = str(uuid.uuid4())
                 #         # Можно захватить полную сумму или частичную
                 #         # captured_payment = Payment.capture(yk_payment_id, {"amount": payment_data.amount}, capture_idempotence_key)
                 #         # logger.info(f"[YooKassa] Платеж {yk_payment_id} успешно захвачен. Новый статус: {captured_payment.status}")
                 #         # Обновить статус заказа соответственно.
                 #     except Exception as capture_error:
                 #         logger.error(f"[YooKassa] Ошибка при попытке захвата платежа {yk_payment_id}: {capture_error}")
            else:
                # Другие статусы: pending, etc. Обычно не требуют активных действий, но их можно логировать.
                logger.info(f"[YooKassa Webhook] Платеж для YooKassa Payment ID: {yk_payment_id} (Order ID: {order.id}) имеет статус '{payment_data.status}'. Дополнительных действий не требуется.")

            return HttpResponse(status=200) # Всегда отвечаем 200 OK на успешно (или ожидаемо) обработанный вебхук
        
        except json.JSONDecodeError:
            logger.error(f"[YooKassa] Ошибка декодирования JSON из тела вебхука. Тело: {request.body[:512]}") # Логируем часть тела для отладки
            return HttpResponse(status=400) # Bad Request
        except BadRequestError as e_sdk: # Ошибка валидации данных от SDK (например, WebhookNotification)
            logger.error(f"[YooKassa] Ошибка валидации данных вебхука от SDK ЮKassa: {e_sdk}. Тело: {request.body[:512]}")
            return HttpResponse(status=400) # Bad Request
        except Exception as e_unexpected:
            # Логируем полную трассировку для неожиданных ошибок
            logger.exception(f"[YooKassa Webhook] НЕПРЕДВИДЕННАЯ КРИТИЧЕСКАЯ ОШИБКА при обработке вебхука. YooKassa Payment ID (если есть): {event_json.get('object', {}).get('id')}, Event Type: {event_json.get('event')}. Тело: {request.body[:1024].decode('utf-8', errors='ignore')}. Ошибка: {e_unexpected}")
            # TODO: Отправка email уведомления администратору об ошибке
            # Пример отправки письма администраторам
            subject = f"Критическая ошибка при обработке YooKassa Webhook - {event_json.get('event')}"
            message_body = (
                f"Произошла непредвиденная ошибка при обработке вебхука от YooKassa.\n\n"
                f"Event Type: {event_json.get('event')}\n"
                f"Object ID (Payment/Refund): {event_json.get('object', {}).get('id')}\n"
                f"Время ошибки: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"
                f"Тело запроса (первые 1024 байта):\n{request.body[:1024].decode('utf-8', errors='ignore')}\n\n"
                f"Сообщение об ошибке:\n{e_unexpected}\n\n"
                f"Пожалуйста, проверьте логи сервера для полной трассировки."
            )
            try:
                mail_admins(subject, message_body, fail_silently=False) # fail_silently=False - вызовет исключение, если отправка не удалась
                logger.info("[YooKassa Webhook] Уведомление об ошибке успешно отправлено администраторам.")
            except Exception as mail_exc:
                logger.error(f"[YooKassa Webhook] НЕ УДАЛОСЬ отправить уведомление об ошибке администраторам. Ошибка отправки: {mail_exc}")

            return HttpResponse(status=500) # Internal Server Error, ЮKassa должна повторить отправку
    
    logger.warning(f"[YooKassa] Вебхук получен с некорректным HTTP методом: {request.method}. Ожидался POST.")
    return HttpResponse(status=405) # Method Not Allowed 