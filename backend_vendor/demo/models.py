from django.db import models
from products.models import Product, Category


class DemoSettings(models.Model):
    """
    Singleton model for demo page configuration.
    Admin can select which products appear in demo pages.
    """
    # Featured products section
    featured_products = models.ManyToManyField(
        Product,
        related_name='demo_featured',
        blank=True,
        help_text="Products to show in the featured section"
    )
    # Flash sale products section
    flash_sale_products = models.ManyToManyField(
        Product,
        related_name='demo_flash_sale',
        blank=True,
        help_text="Products to show in the flash sale section"
    )
    # New arrivals section
    new_arrival_products = models.ManyToManyField(
        Product,
        related_name='demo_new_arrivals',
        blank=True,
        help_text="Products to show in the new arrivals section"
    )
    # All products for main listing
    all_products = models.ManyToManyField(
        Product,
        related_name='demo_all',
        blank=True,
        help_text="All products to show in the demo store"
    )
    # Categories to show
    categories = models.ManyToManyField(
        Category,
        related_name='demo_categories',
        blank=True,
        help_text="Categories to display in the demo"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Demo Settings"
        verbose_name_plural = "Demo Settings"

    def __str__(self):
        return "Demo Page Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion of the singleton
        pass

    @classmethod
    def get_settings(cls):
        """Get or create the singleton DemoSettings instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
