from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product', 'printing_service']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'address', 'status', 'paid', 'paid_at', 'yookassa_payment_id', 'created', 'updated']
    list_filter = ['status', 'paid', 'created', 'updated']
    inlines = [OrderItemInline]
    raw_id_fields = ['user']
    date_hierarchy = 'created'
    ordering = ['-created']
    search_fields = ['user__email', 'address', 'yookassa_payment_id']
    readonly_fields = ['paid_at', 'yookassa_payment_id', 'created', 'updated']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

# Если OrderItem еще не зарегистрирован отдельно (обычно не нужно, если есть Inline)
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ['id', 'order', 'product', 'printing_service', 'price', 'quantity']
#     list_filter = ['order__status'] # Пример фильтра по статусу связанного заказа
#     raw_id_fields = ['order', 'product', 'printing_service']
