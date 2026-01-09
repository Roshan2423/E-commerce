"""
Vendor Signals
Auto-link vendor on login, create storefront on business creation
"""
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Business, VendorStorefront


@receiver(user_logged_in)
def link_vendor_on_login(sender, request, user, **kwargs):
    """
    When a user logs in, check if their email matches a registered business.
    If so, link them as the vendor owner.
    """
    try:
        # Find unlinked business with matching email
        business = Business.objects.get(
            email__iexact=user.email,
            owner__isnull=True,
            status='approved'
        )
        business.owner = user
        business.save()

        # Store in session for redirect notification
        request.session['new_vendor'] = True
        request.session['vendor_business_name'] = business.business_name

        print(f"[Vendor] Linked user {user.email} to business: {business.business_name}")

    except Business.DoesNotExist:
        # No matching business or already linked
        pass


@receiver(post_save, sender=Business)
def create_storefront_for_business(sender, instance, created, **kwargs):
    """
    Automatically create a VendorStorefront when a Business is created.
    """
    if created:
        VendorStorefront.objects.get_or_create(
            business=instance,
            defaults={
                'hero_title': f"Welcome to {instance.business_name}",
                'hero_subtitle': "Discover our amazing products",
            }
        )
        print(f"[Vendor] Created storefront for: {instance.business_name}")


def get_vendor_for_user(user):
    """
    Helper function to get vendor business for a user.
    Returns None if user is not a vendor.
    """
    if not user.is_authenticated:
        return None
    try:
        return Business.objects.get(owner=user, status='approved')
    except Business.DoesNotExist:
        return None


def is_vendor(user):
    """Check if user is an approved vendor"""
    return get_vendor_for_user(user) is not None
