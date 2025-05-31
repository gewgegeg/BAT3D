from django.contrib import admin
from .models import Cart, CartItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'created', 'updated']
    list_filter = ['created', 'updated', 'user']
    search_fields = ['user__username', 'user__email', 'session_key']
    raw_id_fields = ['user']
    date_hierarchy = 'created'

class CartItemInline(admin.TabularInline):
    model = CartItem
    raw_id_fields = ['product', 'printing_service']
    extra = 0
    # Можно добавить readonly_fields, если нужно отображать get_total_price, но это потребует метода в CartItemAdmin

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'printing_service', 'quantity', 'weight', 'printing_time']
    list_filter = ['cart__user', 'product', 'printing_service']
    search_fields = ['cart__user__username', 'product__name', 'printing_service__name']
    raw_id_fields = ['cart', 'product', 'printing_service']

    # Если нужно добавить get_total_price в list_display, раскомментируйте:
    # def display_total_price(self, obj):
    #     return obj.get_total_price()
    # display_total_price.short_description = 'Total Price'

    # И добавьте 'display_total_price' в list_display

# Если вы предпочитаете видеть CartItems встроенными в CartAdmin, раскомментируйте:
# CartAdmin.inlines = [CartItemInline]
# И закомментируйте @admin.register(CartItem) и CartItemAdmin класс, если не нужен отдельный доступ к CartItem.
# Либо оставьте оба варианта регистрации, если это удобно.
