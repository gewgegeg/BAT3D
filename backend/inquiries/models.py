from django.db import models
from django.utils.translation import gettext_lazy as _
from products.models import PrintingService # Assuming PrintingService is in products.models

class ServiceInquiry(models.Model):
    STATUS_CHOICES = [
        ('new', _('New')),
        ('in_progress', _('In Progress')),
        ('contacted', _('Contacted')),
        ('resolved', _('Resolved')),
        ('closed', _('Closed')),
    ]

    service = models.ForeignKey(
        PrintingService, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name=_("Service"),
        help_text=_("The specific printing service this inquiry is about, if any.")
    )
    name = models.CharField(_("Name"), max_length=255)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Phone Number"), max_length=30, blank=True)
    message = models.TextField(_("Message"))
    status = models.CharField(
        _("Status"), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='new'
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Service Inquiry")
        verbose_name_plural = _("Service Inquiries")
        ordering = ['-created_at']

    def __str__(self):
        service_name = self.service.name if self.service else _("General Inquiry")
        return _("Inquiry from %(name)s for %(service)s (%(status)s)") % {
            'name': self.name, 
            'service': service_name, 
            'status': self.get_status_display()
        }
