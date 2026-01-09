"""
Vendor Context Processors
Provides vendor-related data to all templates
"""
from .models import Business, VendorMessage, VendorApplication, VendorStorefront


def dashboard_theme(request):
    """
    Inject dashboard theme colors for professional plan vendors.
    These CSS variables can be used in vendor dashboard templates.
    """
    if not request.user.is_authenticated:
        return {'dashboard_theme': None}

    try:
        # Get user's business
        business = Business.objects.filter(owner=request.user, status='approved').first()

        if not business:
            return {'dashboard_theme': None}

        # Only apply custom theme for professional plan
        if business.plan != 'professional':
            return {'dashboard_theme': None}

        # Get storefront settings
        storefront = VendorStorefront.objects.filter(business=business).first()

        if storefront:
            return {
                'dashboard_theme': {
                    'sidebar': storefront.dashboard_sidebar_color or '#111827',
                    'primary': storefront.dashboard_primary_color or '#6366f1',
                    'accent': storefront.dashboard_accent_color or '#10b981',
                }
            }

    except Exception:
        pass

    return {'dashboard_theme': None}


def vendor_context(request):
    """
    Add vendor business and related data to template context
    """
    context = {
        'vendor_business': None,
        'is_vendor': False,
        'pending_orders_count': 0,
        'unread_vendor_messages_count': 0,
        'pending_applications_count': 0,
    }

    if not request.user.is_authenticated:
        return context

    try:
        # For admin users, show pending applications count
        if request.user.is_superuser or request.user.is_staff:
            pending_apps = VendorApplication.objects.filter(status='pending').count()
            context['pending_applications_count'] = pending_apps

        # Check if user has a business
        business = Business.objects.filter(owner=request.user, status='approved').first()
        if business:
            context['vendor_business'] = business
            context['is_vendor'] = True

            # Get pending orders count
            from orders.models import OrderItem
            pending_orders = OrderItem.objects.filter(
                vendor=business,
                order__status='processing'
            ).count()
            context['pending_orders_count'] = pending_orders

            # Get unread messages count
            unread_messages = VendorMessage.objects.filter(
                business=business,
                is_read=False,
                is_from_vendor=False
            ).count()
            context['unread_vendor_messages_count'] = unread_messages

    except Exception:
        pass

    return context
