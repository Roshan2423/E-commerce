"""
Django Signals for MongoDB Sync
Automatically syncs all model changes to MongoDB
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps

from .mongodb_sync import (
    sync_product, sync_category, sync_product_image,
    sync_order, sync_order_item, sync_user, sync_review, sync_contact
)


def connect_signals():
    """Connect all model signals for MongoDB sync"""

    # Product signals
    try:
        Product = apps.get_model('products', 'Product')

        @receiver(post_save, sender=Product)
        def product_saved(sender, instance, **kwargs):
            sync_product(instance)

        @receiver(post_delete, sender=Product)
        def product_deleted(sender, instance, **kwargs):
            sync_product(instance, deleted=True)

        print("[MongoDB Sync] Product signals connected")
    except Exception as e:
        print(f"[MongoDB Sync] Could not connect Product signals: {e}")

    # Category signals
    try:
        Category = apps.get_model('products', 'Category')

        @receiver(post_save, sender=Category)
        def category_saved(sender, instance, **kwargs):
            sync_category(instance)

        @receiver(post_delete, sender=Category)
        def category_deleted(sender, instance, **kwargs):
            sync_category(instance, deleted=True)

        print("[MongoDB Sync] Category signals connected")
    except Exception as e:
        print(f"[MongoDB Sync] Could not connect Category signals: {e}")

    # ProductImage signals
    try:
        ProductImage = apps.get_model('products', 'ProductImage')

        @receiver(post_save, sender=ProductImage)
        def product_image_saved(sender, instance, **kwargs):
            sync_product_image(instance)

        @receiver(post_delete, sender=ProductImage)
        def product_image_deleted(sender, instance, **kwargs):
            sync_product_image(instance, deleted=True)

        print("[MongoDB Sync] ProductImage signals connected")
    except Exception as e:
        print(f"[MongoDB Sync] Could not connect ProductImage signals: {e}")

    # Order signals
    try:
        Order = apps.get_model('orders', 'Order')

        @receiver(post_save, sender=Order)
        def order_saved(sender, instance, **kwargs):
            sync_order(instance)

        @receiver(post_delete, sender=Order)
        def order_deleted(sender, instance, **kwargs):
            sync_order(instance, deleted=True)

        print("[MongoDB Sync] Order signals connected")
    except Exception as e:
        print(f"[MongoDB Sync] Could not connect Order signals: {e}")

    # OrderItem signals
    try:
        OrderItem = apps.get_model('orders', 'OrderItem')

        @receiver(post_save, sender=OrderItem)
        def order_item_saved(sender, instance, **kwargs):
            sync_order_item(instance)

        @receiver(post_delete, sender=OrderItem)
        def order_item_deleted(sender, instance, **kwargs):
            sync_order_item(instance, deleted=True)

        print("[MongoDB Sync] OrderItem signals connected")
    except Exception as e:
        print(f"[MongoDB Sync] Could not connect OrderItem signals: {e}")

    # User signals
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        @receiver(post_save, sender=User)
        def user_saved(sender, instance, **kwargs):
            sync_user(instance)

        @receiver(post_delete, sender=User)
        def user_deleted(sender, instance, **kwargs):
            sync_user(instance, deleted=True)

        print("[MongoDB Sync] User signals connected")
    except Exception as e:
        print(f"[MongoDB Sync] Could not connect User signals: {e}")

    # Review signals
    try:
        Review = apps.get_model('products', 'Review')

        @receiver(post_save, sender=Review)
        def review_saved(sender, instance, **kwargs):
            sync_review(instance)

        @receiver(post_delete, sender=Review)
        def review_deleted(sender, instance, **kwargs):
            sync_review(instance, deleted=True)

        print("[MongoDB Sync] Review signals connected")
    except Exception as e:
        pass  # Review model might not exist

    # Contact signals
    try:
        Contact = apps.get_model('contacts', 'Contact')

        @receiver(post_save, sender=Contact)
        def contact_saved(sender, instance, **kwargs):
            sync_contact(instance)

        @receiver(post_delete, sender=Contact)
        def contact_deleted(sender, instance, **kwargs):
            sync_contact(instance, deleted=True)

        print("[MongoDB Sync] Contact signals connected")
    except Exception as e:
        pass  # Contact model might not exist
