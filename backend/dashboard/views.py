from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from products.models import Product, Category
from orders.models import Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require admin/staff access"""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/dashboard/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Simple counts without complex aggregations
            context['total_products'] = Product.objects.count()
            context['total_orders'] = Order.objects.count()
            context['total_customers'] = User.objects.filter(is_staff=False).count()
            
            # Calculate revenue from actual orders
            total_revenue = 0
            try:
                for order in Order.objects.filter(payment_status='paid'):
                    total_revenue += order.total_amount or 0
            except:
                total_revenue = 0
            context['total_revenue'] = total_revenue
            
            # Simple percentage calculations
            context['orders_change'] = 0
            context['revenue_change'] = 0
            context['this_month_orders'] = context['total_orders']
            context['this_month_revenue'] = total_revenue
            
            # Recent orders (limited to avoid complex queries)
            context['recent_orders'] = Order.objects.order_by('-id')[:5]
            
            # Low stock products (simple query)
            context['low_stock_products'] = Product.objects.filter(stock_quantity__lte=10)[:5]
            
            # Order status data
            context['order_status_stats'] = []
            
            # Top products
            context['top_products'] = Product.objects.order_by('-id')[:5]
            
        except Exception as e:
            # If database queries fail, provide empty data
            context.update({
                'total_products': 0,
                'total_orders': 0,
                'total_customers': 0,
                'total_revenue': 0,
                'orders_change': 0,
                'revenue_change': 0,
                'recent_orders': [],
                'low_stock_products': [],
                'order_status_stats': [],
                'top_products': []
            })
        
        return context


class DashboardOverviewView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/dashboard/overview.html'