from django.db import models
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    description = models.TextField(_('description'), blank=True)
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('category')
    )
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    image = models.ImageField(_('image'), upload_to='products/%Y/%m/%d/', blank=True, null=True)
    description = models.TextField(_('description'), blank=True)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(_('stock'))
    available = models.BooleanField(_('available'), default=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    updated = models.DateTimeField(_('updated'), auto_now=True)
    
    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class PrintingMaterial(models.Model):
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'))
    price_multiplier = models.DecimalField(_('price multiplier'), max_digits=4, decimal_places=2)
    color = models.CharField(_('color'), max_length=50)
    properties = models.TextField(_('properties'), blank=True, default='')
    
    class Meta:
        verbose_name = _('printing material')
        verbose_name_plural = _('printing materials')
        ordering = ['name']
    
    def get_properties(self):
        return [p.strip() for p in self.properties.split(',') if p.strip()]
    
    def set_properties(self, properties_list):
        self.properties = ','.join(properties_list)
    
    def __str__(self):
        return self.name

class PrintingService(models.Model):
    # ICON_CHOICES = [
    #     ('speed', 'Fast Printing'),
    #     ('quality', 'High Quality'),
    #     ('modeling', '3D Modeling'),
    #     ('painting', 'Painting'),
    #     ('support', 'Support'),
    #     ('delivery', 'Delivery'),
    # ]

    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'))
    base_price = models.DecimalField(_('base price'), max_digits=10, decimal_places=2)
    # price_per_gram = models.DecimalField(_('price per gram'), max_digits=10, decimal_places=2) # Removed from admin form
    # price_per_hour = models.DecimalField(_('price per hour'), max_digits=10, decimal_places=2) # Removed from admin form
    min_weight = models.DecimalField(_('minimum weight'), max_digits=10, decimal_places=2, default=10.00)
    max_weight = models.DecimalField(_('maximum weight'), max_digits=10, decimal_places=2, default=1000.00)
    available = models.BooleanField(_('available'), default=True)
    features = models.TextField(_('features'), blank=True, default='')
    # icon = models.CharField(_('icon'), max_length=50, choices=ICON_CHOICES, default='speed') # Old icon field
    # icon = models.ImageField(_('icon'), upload_to='service_icons/', blank=True, null=True) # New icon field
    image = models.ImageField(_('image'), upload_to='service_images/', blank=True, null=True) # Changed from icon, removed redundant verbose_name
    materials = models.ManyToManyField(
        PrintingMaterial,
        related_name='services',
        verbose_name=_('materials'),
        blank=True
    )
    estimated_delivery_days = models.PositiveIntegerField(_('estimated delivery days'), default=3)
    
    class Meta:
        verbose_name = _('printing service')
        verbose_name_plural = _('printing services')
        ordering = ['name']
    
    def get_features(self):
        return [f.strip() for f in self.features.split(',') if f.strip()]
    
    def set_features(self, features_list):
        self.features = ','.join(features_list)
    
    def __str__(self):
        return self.name
