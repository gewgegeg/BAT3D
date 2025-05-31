from django.db import models
from django.conf import settings
from products.models import Product, PrintingService

class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f'Cart {self.id} for {self.user.username}'
        else:
            return f'Cart {self.id} for anonymous user'

    def clear_cart(self):
        """Удаляет все товары из корзины."""
        self.items.all().delete()

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    printing_service = models.ForeignKey(
        PrintingService,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    printing_time = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'CartItem {self.id}'

    def get_total_price(self):
        if self.product:
            return self.product.price * self.quantity
        elif self.printing_service:
            base_price = self.printing_service.base_price
            if self.weight:
                base_price += self.printing_service.price_per_gram * self.weight
            if self.printing_time:
                base_price += self.printing_service.price_per_hour * self.printing_time
            return base_price * self.quantity
        return 0
