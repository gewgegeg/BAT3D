from django.urls import path
from .yookassa_handlers import CreateYookassaPaymentView, yookassa_return_url_view, yookassa_webhook_view

app_name = 'payments' # Это важно для именования URL-маршрутов
 
urlpatterns = [
    path('yookassa/create/<int:order_id>/', CreateYookassaPaymentView.as_view(), name='yookassa_create_payment'),
    path('yookassa/return/<int:order_id>/', yookassa_return_url_view, name='yookassa_return_url'),
    path('yookassa/webhook/', yookassa_webhook_view, name='yookassa_webhook'),
] 