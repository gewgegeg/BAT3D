from django.contrib import admin
from .models import HomePageSettings, HeroSlideImage, AboutUsImage, WorkGalleryImage

@admin.register(HomePageSettings)
class HomePageSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_featured_products_preview', 'get_featured_services_preview')
    # readonly_fields = ('id',)

    def get_featured_products_preview(self, obj):
        return ", ".join(obj.featured_products[:5]) + ('...' if len(obj.featured_products) > 5 else '')
    get_featured_products_preview.short_description = 'Featured Products (Preview)'

    def get_featured_services_preview(self, obj):
        return ", ".join(obj.featured_services[:5]) + ('...' if len(obj.featured_services) > 5 else '')
    get_featured_services_preview.short_description = 'Featured Services (Preview)'

    def has_add_permission(self, request):
        # Prevent adding new instances if one already exists (singleton pattern)
        return not HomePageSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Optionally, prevent deletion of the singleton instance
        return False # Or True if you want to allow deletion and recreation

# Note: Since it's a singleton, typical admin actions like add/delete might be restricted.
# The `load()` method in the model ensures an instance is available.
# If you allow deletion, ensure the `load()` method correctly handles recreation or that you manually recreate it.

@admin.register(HeroSlideImage)
class HeroSlideImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'order')
    list_editable = ('order',)
    # Add other configurations as needed, e.g., for image previews

@admin.register(AboutUsImage)
class AboutUsImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'order')
    list_editable = ('order',)

@admin.register(WorkGalleryImage)
class WorkGalleryImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'title', 'order', 'link') # Added title and link to display
    list_editable = ('order', 'title', 'link') # Added title and link as editable
    search_fields = ('title', 'description')
    list_filter = ('order',)
