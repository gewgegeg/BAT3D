from django.db import models
from django.utils.translation import gettext_lazy as _

class Review(models.Model):
    author_name = models.CharField(_("Author Name"), max_length=100)
    review_text = models.TextField(_("Review Text"))
    source_link = models.URLField(_("Source Link"), blank=True, null=True, help_text=_("Link to the original review (e.g., Avito, Yandex Maps, etc.)"))
    rating = models.PositiveSmallIntegerField(_("Rating"), blank=True, null=True, help_text=_("Rating from 1 to 5 stars"))
    is_visible = models.BooleanField(_("Is Visible"), default=True, help_text=_("Should this review be displayed on the site?"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.author_name}" 