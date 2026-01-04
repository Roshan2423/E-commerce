from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from products.models import Product, Category
from orders.models import Order, OrderItem
from django.contrib.auth import get_user_model
from ecommerce.mixins import AdminRequiredMixin
from ecommerce.groq_utils import get_groq_usage, format_token_count

User = get_user_model()


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


@staff_member_required
@require_GET
def groq_usage_api(request):
    """API endpoint to get Groq API usage stats"""
    try:
        usage = get_groq_usage()

        # Format for display
        response_data = {
            'success': True,
            'available': usage.get('available', False),
            'remaining_requests': usage.get('remaining_requests', 0),
            'remaining_tokens': usage.get('remaining_tokens', 0),
            'remaining_tokens_formatted': format_token_count(usage.get('remaining_tokens', 0)),
            'limit_requests': usage.get('limit_requests', 30),
            'limit_tokens': usage.get('limit_tokens', 30000),
            'limit_tokens_formatted': format_token_count(usage.get('limit_tokens', 30000)),
            'requests_percent': usage.get('requests_percent', 0),
            'tokens_percent': usage.get('tokens_percent', 0),
            'last_checked': usage.get('last_checked', ''),
            'error': usage.get('error', '')
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'available': False,
            'remaining_tokens': 0,
            'remaining_tokens_formatted': '0',
            'tokens_percent': 0
        })