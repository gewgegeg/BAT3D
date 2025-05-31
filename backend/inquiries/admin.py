from django.contrib import admin
from .models import ServiceInquiry

@admin.register(ServiceInquiry)
class ServiceInquiryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'email', 'phone', 'service', 
        'status', 'created_at', 'updated_at'
    )
    list_filter = ('status', 'service', 'created_at')
    search_fields = ('name', 'email', 'phone', 'message', 'service__name')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'phone', 'service', 'message')
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('service')
