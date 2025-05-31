from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'rating', 'is_visible', 'created_at', 'source_link')
    list_filter = ('is_visible', 'rating', 'created_at')
    search_fields = ('author_name', 'review_text')
    list_editable = ('is_visible', 'rating')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('author_name', 'review_text', 'source_link', 'rating', 'is_visible')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 