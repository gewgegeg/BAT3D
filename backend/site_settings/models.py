from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class HomePageSettings(models.Model):
    """
    Model to store settings for the home page, ensuring only one instance exists.
    """
    featured_products = models.JSONField(
        _("featured products"),
        default=list,
        blank=True,
        help_text=_("List of product IDs or slugs to feature on the home page.")
    )
    featured_services = models.JSONField(
        _("featured services"),
        default=list,
        blank=True,
        help_text=_("List of service IDs or slugs to feature on the home page.")
    )
    # Add other fields for home page settings here, e.g.:
    # hero_title = models.CharField(max_length=200, blank=True)
    # hero_subtitle = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Home Page Settings")
        verbose_name_plural = _("Home Page Settings")

    def __str__(self):
        return _("Home Page Settings")

    def save(self, *args, **kwargs):
        if not self.pk and HomePageSettings.objects.exists():
            # Prevent creation of a new instance if one already exists
            raise ValidationError(_('There can be only one instance of Home Page Settings.'))
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Load the singleton instance, creating it if it doesn't exist."""
        obj, created = cls.objects.get_or_create(pk=1) # Assuming pk=1 for the single instance
        return obj

class OrderedImageModel(models.Model):
    image = models.ImageField(_("image"), upload_to='site_content/%Y/%m/%d/')
    order = models.PositiveIntegerField(
        _("order"),
        default=0,
        db_index=True,
        help_text=_("Order in which the image appears. Lower numbers appear first.")
    )

    class Meta:
        abstract = True
        ordering = ['order']

    def __str__(self):
        return f"Image (Order: {self.order}) - {self.image.name}"

class HeroSlideImage(OrderedImageModel):
    class Meta(OrderedImageModel.Meta):
        verbose_name = _("Hero Slide Image")
        verbose_name_plural = _("Hero Slide Images")
        # Add default_related_name to avoid clashes if this model is related to others
        # default_related_name = 'hero_slide_images'

class AboutUsImage(OrderedImageModel):
    class Meta(OrderedImageModel.Meta):
        verbose_name = _("About Us Image")
        verbose_name_plural = _("About Us Images")
        # default_related_name = 'about_us_images'

class WorkGalleryImage(OrderedImageModel):
    title = models.CharField(_("title"), max_length=200, blank=True, help_text=_("Optional title for the work."))
    description = models.TextField(_("description"), blank=True, help_text=_("Optional description for the work."))
    link = models.URLField(_("link"), blank=True, help_text=_("Optional link related to the work."))

    class Meta(OrderedImageModel.Meta):
        verbose_name = _("Work Gallery Image")
        verbose_name_plural = _("Work Gallery Images")
        # default_related_name = 'work_gallery_images'

    def __str__(self):
        return self.title if self.title else super().__str__()
