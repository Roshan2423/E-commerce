"""
Customer Dashboard Views
Cloudflare-style dashboard for customer account management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator

from orders.models import Order, OrderItem
from products.models import Review
from .models import User, Address


class CustomerDashboardMixin(LoginRequiredMixin):
    """Mixin for customer dashboard views"""
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dashboard_type'] = 'customer'
        return context


class DashboardOverviewView(CustomerDashboardMixin, TemplateView):
    """Customer dashboard overview/home page"""
    template_name = 'account/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get order stats
        orders = Order.objects.filter(user=user, is_deleted=False)
        context['total_orders'] = orders.count()
        context['pending_orders'] = orders.filter(status__in=['processing', 'confirmed', 'packed']).count()
        context['shipped_orders'] = orders.filter(status='shipped').count()
        context['delivered_orders'] = orders.filter(status='delivered').count()

        # Total spent
        context['total_spent'] = orders.filter(payment_status='paid').aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        # Recent orders (last 5)
        context['recent_orders'] = orders[:5]

        # Review count
        context['review_count'] = Review.objects.filter(user=user).count()

        # Address count
        context['address_count'] = Address.objects.filter(user=user).count()

        return context


class OrderListView(CustomerDashboardMixin, ListView):
    """List all customer orders"""
    template_name = 'account/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        queryset = Order.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['status_choices'] = Order.STATUS_CHOICES
        return context


class OrderDetailView(CustomerDashboardMixin, DetailView):
    """View single order details"""
    template_name = 'account/orders/detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_deleted=False)

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            order_id=self.kwargs['order_id']
        )


class AddressListView(CustomerDashboardMixin, ListView):
    """List all customer addresses"""
    template_name = 'account/addresses/list.html'
    context_object_name = 'addresses'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressCreateView(CustomerDashboardMixin, CreateView):
    """Create new address"""
    template_name = 'account/addresses/form.html'
    model = Address
    fields = ['address_type', 'street_address', 'apartment', 'city', 'state', 'postal_code', 'country', 'is_default']
    success_url = reverse_lazy('customer_dashboard:addresses')

    def form_valid(self, form):
        form.instance.user = self.request.user

        # If setting as default, unset other defaults
        if form.cleaned_data.get('is_default'):
            Address.objects.filter(
                user=self.request.user,
                address_type=form.cleaned_data['address_type'],
                is_default=True
            ).update(is_default=False)

        messages.success(self.request, 'Address added successfully!')
        return super().form_valid(form)


class AddressUpdateView(CustomerDashboardMixin, UpdateView):
    """Update existing address"""
    template_name = 'account/addresses/form.html'
    model = Address
    fields = ['address_type', 'street_address', 'apartment', 'city', 'state', 'postal_code', 'country', 'is_default']
    success_url = reverse_lazy('customer_dashboard:addresses')

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def form_valid(self, form):
        if form.cleaned_data.get('is_default'):
            Address.objects.filter(
                user=self.request.user,
                address_type=form.cleaned_data['address_type'],
                is_default=True
            ).exclude(pk=self.object.pk).update(is_default=False)

        messages.success(self.request, 'Address updated successfully!')
        return super().form_valid(form)


class AddressDeleteView(CustomerDashboardMixin, DeleteView):
    """Delete an address"""
    model = Address
    success_url = reverse_lazy('customer_dashboard:addresses')

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Address deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ReviewListView(CustomerDashboardMixin, ListView):
    """List all customer reviews"""
    template_name = 'account/reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user).order_by('-created_at')


class ProfileView(CustomerDashboardMixin, TemplateView):
    """View and edit profile settings"""
    template_name = 'account/settings/profile.html'


class ProfileUpdateView(CustomerDashboardMixin, UpdateView):
    """Update profile information"""
    template_name = 'account/settings/profile.html'
    model = User
    fields = ['first_name', 'last_name', 'phone_number', 'date_of_birth']
    success_url = reverse_lazy('customer_dashboard:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class SettingsView(CustomerDashboardMixin, TemplateView):
    """Account settings page"""
    template_name = 'account/settings/settings.html'


# API Views for AJAX operations
@login_required
def api_dashboard_stats(request):
    """Return dashboard statistics as JSON"""
    user = request.user
    orders = Order.objects.filter(user=user, is_deleted=False)

    stats = {
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status__in=['processing', 'confirmed', 'packed']).count(),
        'delivered_orders': orders.filter(status='delivered').count(),
        'total_spent': float(orders.filter(payment_status='paid').aggregate(
            total=Sum('total_amount')
        )['total'] or 0),
        'review_count': Review.objects.filter(user=user).count(),
    }

    return JsonResponse(stats)
