from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from .models import Order, OrderItem, ShippingMethod
from .forms import OrderUpdateForm


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require admin/staff access"""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class OrderListView(AdminRequiredMixin, ListView):
    model = Order
    template_name = 'admin/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        try:
            queryset = Order.objects.all()
            
            # Search functionality
            search = self.request.GET.get('search')
            if search:
                queryset = queryset.filter(order_id__icontains=search)
            
            # Status filter
            status = self.request.GET.get('status')
            if status:
                queryset = queryset.filter(status=status)
                
            # Payment status filter
            payment_status = self.request.GET.get('payment_status')
            if payment_status:
                queryset = queryset.filter(payment_status=payment_status)
            
            return queryset.order_by('-id')
        except:
            return Order.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_payment_status'] = self.request.GET.get('payment_status', '')
        context['status_choices'] = Order.STATUS_CHOICES
        context['payment_status_choices'] = Order.PAYMENT_STATUS_CHOICES
        return context


class OrderDetailView(AdminRequiredMixin, DetailView):
    model = Order
    template_name = 'admin/orders/detail.html'
    context_object_name = 'order'
    slug_field = 'order_id'
    slug_url_kwarg = 'order_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['order_items'] = self.object.items.all()
        except:
            context['order_items'] = []
        return context


class OrderUpdateView(AdminRequiredMixin, UpdateView):
    model = Order
    template_name = 'admin/orders/update.html'
    fields = ['status', 'payment_status', 'shipping_method', 'tracking_number', 'notes']
    slug_field = 'order_id'
    slug_url_kwarg = 'order_id'
    
    def get_success_url(self):
        return f'/orders/{self.object.order_id}/'
    
    def form_valid(self, form):
        order = form.save(commit=False)
        
        # Update timestamps based on status changes
        if 'status' in form.changed_data:
            if order.status == 'shipped' and not order.shipped_at:
                order.shipped_at = timezone.now()
            elif order.status == 'delivered' and not order.delivered_at:
                order.delivered_at = timezone.now()
        
        order.save()
        messages.success(self.request, f'Order {order.get_order_number()} updated successfully!')
        return super().form_valid(form)


class OrderCancelView(AdminRequiredMixin, DetailView):
    model = Order
    slug_field = 'order_id'
    slug_url_kwarg = 'order_id'
    
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        
        if order.status in ['pending', 'confirmed']:
            order.status = 'cancelled'
            order.save()
            messages.success(request, f'Order {order.get_order_number()} has been cancelled.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
            
        return redirect(f'/orders/{order.order_id}/')