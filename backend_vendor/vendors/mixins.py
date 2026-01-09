"""
Vendor Access Control Mixins
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from .models import Business


def get_vendor_business(user, vendor_id=None):
    """Helper function to get vendor's business for function-based views.
    Returns None if user is not an approved vendor.

    For admins: Must specify vendor_id or have their own business.
    For vendors: Returns their own business only.
    """
    if not user.is_authenticated:
        return None

    # If vendor_id is specified and user is admin, get that specific vendor
    if vendor_id and (user.is_staff or user.is_superuser):
        try:
            return Business.objects.get(pk=vendor_id, status='approved')
        except Business.DoesNotExist:
            return None

    # Try to get the user's own business
    try:
        return Business.objects.get(owner=user, status='approved')
    except Business.DoesNotExist:
        # Admins without their own business cannot access vendor functions
        # unless they specify a vendor_id
        return None


class VendorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to require vendor access for views.
    User must be logged in AND be an approved vendor OR be an admin.
    Admins can access any vendor's dashboard via ?vendor_id=X parameter.
    """
    login_url = '/login/'
    permission_denied_message = "You need to be a registered vendor to access this page."

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False

        # Admin users can always access
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True

        # Regular users need to be approved vendors
        try:
            business = Business.objects.get(
                owner=self.request.user,
                status='approved'
            )
            return True
        except Business.DoesNotExist:
            return False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(f'{self.login_url}?next={self.request.path}')

        # User authenticated but not a vendor
        messages.error(
            self.request,
            "You don't have access to the vendor dashboard. "
            "Please contact support if you believe this is an error."
        )
        return redirect('/')

    def get_vendor_business(self):
        """Helper to get the current vendor's business.
        Admins can specify vendor_id parameter to manage any vendor.

        SECURITY: Never falls back to another vendor's business.
        Admins must explicitly specify vendor_id or have their own business.
        """
        user = self.request.user

        # Admin can access any vendor via query parameter
        if user.is_staff or user.is_superuser:
            vendor_id = self.request.GET.get('vendor_id') or self.request.session.get('admin_vendor_id')
            if vendor_id:
                try:
                    business = Business.objects.get(pk=vendor_id, status='approved')
                    business.refresh_from_db()  # Ensure fresh data
                    return business
                except Business.DoesNotExist:
                    pass
            # If no vendor_id specified, try to get admin's own business only
            # DO NOT fall back to first available vendor - this causes data leakage
            try:
                business = Business.objects.get(owner=user, status='approved')
                business.refresh_from_db()  # Ensure fresh data
                return business
            except Business.DoesNotExist:
                # Admin without own business must specify vendor_id
                raise Business.DoesNotExist("Admin must specify vendor_id or have their own business")

        # Regular vendor - return their own business only
        business = Business.objects.get(owner=user, status='approved')
        business.refresh_from_db()  # Ensure fresh data
        return business

    def is_admin_managing(self):
        """Check if admin is managing a vendor (not their own business)"""
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            return False
        try:
            business = self.get_vendor_business()
            return business.owner != user
        except Business.DoesNotExist:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['business'] = self.get_vendor_business()
            context['storefront'] = context['business'].storefront
            context['is_admin_managing'] = self.is_admin_managing()
            # Admin bypass - no subscription restrictions
            context['admin_bypass'] = self.request.user.is_staff or self.request.user.is_superuser

            # Flash sale count for sidebar badge
            from products.models import Product
            context['flash_sale_count'] = Product.objects.filter(
                vendor=context['business'],
                is_active=True,
                is_flash_sale=True
            ).count()
        except (Business.DoesNotExist, AttributeError):
            pass
        return context


class VendorOwnerMixin:
    """
    Mixin to ensure vendor can only access their own objects.
    Use with VendorRequiredMixin.
    """
    vendor_field = 'vendor'  # Field name linking to Business model

    def get_queryset(self):
        queryset = super().get_queryset()
        business = self.get_vendor_business()
        filter_kwargs = {self.vendor_field: business}
        return queryset.filter(**filter_kwargs)


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin for super admin views (existing functionality).
    """
    login_url = '/login/'

    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(f'{self.login_url}?next={self.request.path}')
        messages.error(self.request, "You don't have admin access.")
        return redirect('/')
