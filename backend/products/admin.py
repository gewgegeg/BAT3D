from django.contrib import admin
from .models import Category, Product, PrintingService, PrintingMaterial
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    ordering = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'price', 'stock', 'available', 'created', 'updated']
    list_filter = ['available', 'created', 'updated', 'category']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    raw_id_fields = ['category']
    date_hierarchy = 'created'
    ordering = ['name']

@admin.register(PrintingMaterial)
class PrintingMaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_multiplier', 'color']
    list_filter = ['price_multiplier']
    list_editable = ['price_multiplier', 'color']
    search_fields = ['name', 'description', 'properties']
    ordering = ['name']

@admin.register(PrintingService)
class PrintingServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price', 'image_preview', 'available', 'estimated_delivery_days']
    list_filter = ['available', 'materials']
    list_editable = ['base_price', 'available', 'estimated_delivery_days']
    search_fields = ['name', 'description', 'features']
    filter_horizontal = ['materials']
    ordering = ['name']
    fields = ('name', 'description', 'image', 'base_price', 'min_weight', 'max_weight', 'available', 'features', 'materials', 'estimated_delivery_days')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = 'Изображение'
