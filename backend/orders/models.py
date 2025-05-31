from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from products.models import Product, PrintingService

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending Payment')),          # Ожидает оплаты (начальный статус)
        ('processing', _('Принят (оплачен)')),      # Платеж успешно обработан, заказ принят
        ('in_progress', _('В работе')),            # Заказ находится в процессе выполнения
        ('awaiting_shipment', _('Готов к отправке/выдаче')), # Укомплектован, ожидает отправки/выдачи
        ('shipped', _('Отправлен')),
        ('delivered', _('Доставлен')),
        ('cancelled', _('Отменен')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('user')
    )
    address = models.TextField(_('delivery address'))
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='processing' # Статус по умолчанию при создании заказа изменен на 'processing'
    )
    paid = models.BooleanField(_('paid'), default=False)
    stripe_payment_id = models.CharField(
        _('Stripe payment ID'),
        max_length=250,
        blank=True
    )
    yookassa_payment_id = models.CharField(
        _('YooKassa payment ID'),
        max_length=250,
        blank=True,
        null=True
    )
    paid_at = models.DateTimeField(
        _('payment confirmation time'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created']
    
    def __str__(self):
        return f'Order {self.id}'
    
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name=_('product'),
        null=True,
        blank=True
    )
    printing_service = models.ForeignKey(
        PrintingService,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name=_('printing service'),
        null=True,
        blank=True
    )
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    
    # Дополнительные поля для услуг печати
    weight = models.DecimalField(
        _('weight (g)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    printing_time = models.DecimalField(
        _('printing time (hours)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
    
    def __str__(self):
        return str(self.id)
    
    def get_cost(self):
        if self.product:
            return self.price * self.quantity
        elif self.printing_service:
            base_cost = self.printing_service.base_price
            weight_cost = self.printing_service.price_per_gram * (self.weight or 0)
            time_cost = self.printing_service.price_per_hour * (self.printing_time or 0)
            return base_cost + weight_cost + time_cost
        return 0
