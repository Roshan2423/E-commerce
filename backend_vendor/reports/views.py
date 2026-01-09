from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q, F, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from products.models import Product, Category
from orders.models import Order, OrderItem
from django.contrib.auth import get_user_model
from ecommerce.mixins import AdminRequiredMixin
import json

User = get_user_model()


class ReportsHomeView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/reports/home.html'


class SalesReportView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/reports/sales.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date range from request or default to last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            
        context['date_from'] = start_date
        context['date_to'] = end_date
        
        # Filter orders by date range and payment status
        orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            payment_status='paid'
        )
        
        # Sales summary
        context['total_sales'] = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        context['total_orders'] = orders.count()
        context['average_order_value'] = orders.aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Daily sales data for chart
        daily_sales = orders.values('created_at__date').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('created_at__date')
        
        context['daily_sales_data'] = json.dumps(list(daily_sales), default=str)
        
        # Top selling products
        top_products = Product.objects.filter(
            orderitem__order__in=orders
        ).annotate(
            total_sold=Sum('orderitem__quantity'),
            revenue=Sum(F('orderitem__quantity') * F('orderitem__unit_price'))
        ).order_by('-revenue')[:10]
        
        context['top_products'] = top_products
        
        return context


class ProductReportView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/reports/products.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Product statistics
        context['total_products'] = Product.objects.filter(is_active=True).count()
        context['low_stock_products'] = Product.objects.filter(
            stock_quantity__lte=F('low_stock_threshold'),
            is_active=True
        ).count()
        context['out_of_stock_products'] = Product.objects.filter(
            stock_quantity=0,
            is_active=True
        ).count()
        
        # Category-wise product distribution
        category_stats = Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('-product_count')
        
        context['category_stats'] = category_stats
        
        # Most viewed/sold products (top 20)
        best_sellers = Product.objects.annotate(
            total_sold=Sum('orderitem__quantity')
        ).filter(total_sold__isnull=False).order_by('-total_sold')[:20]
        
        context['best_sellers'] = best_sellers
        
        # Products that need attention (low stock, no sales, etc.)
        attention_products = Product.objects.filter(
            Q(stock_quantity__lte=F('low_stock_threshold')) |
            Q(stock_quantity=0)
        ).filter(is_active=True)[:20]
        
        context['attention_products'] = attention_products
        
        return context


class CustomerReportView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/reports/customers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Customer statistics
        context['total_customers'] = User.objects.filter(is_active=True, is_staff=False).count()
        context['customers_with_orders'] = User.objects.filter(
            orders__isnull=False,
            is_active=True,
            is_staff=False
        ).distinct().count()
        
        # Top customers by order value
        top_customers = User.objects.filter(
            is_active=True,
            is_staff=False
        ).annotate(
            total_spent=Sum('orders__total_amount', filter=Q(orders__payment_status='paid')),
            order_count=Count('orders')
        ).filter(total_spent__isnull=False).order_by('-total_spent')[:20]
        
        context['top_customers'] = top_customers
        
        # Customer acquisition over time (last 12 months)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        monthly_customers = User.objects.filter(
            date_joined__date__gte=start_date,
            is_active=True,
            is_staff=False
        ).values(
            'date_joined__year', 
            'date_joined__month'
        ).annotate(
            count=Count('id')
        ).order_by('date_joined__year', 'date_joined__month')
        
        context['monthly_customers_data'] = json.dumps(list(monthly_customers), default=str)
        
        # Recent customers
        recent_customers = User.objects.filter(
            is_active=True,
            is_staff=False
        ).order_by('-date_joined')[:10]
        
        context['recent_customers'] = recent_customers
        
        return context