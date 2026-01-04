from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json

from .models import Order, OrderItem, OrderHistory
from products.models import Product


@csrf_exempt
@require_http_methods(["POST"])
def create_frontend_order(request):
    """API endpoint for creating orders from frontend - supports guest checkout"""
    try:
        data = json.loads(request.body)

        # Get customer details
        customer_name = data.get('customer_name', '').strip()
        contact_number = data.get('contact_number', '').strip()
        location = data.get('location', '').strip()
        landmark = data.get('landmark', '').strip()
        payment_method = data.get('payment_method', 'cod')
        notes = data.get('notes', '').strip()
        guest_email = data.get('email', '').strip()
        delivery_charge = Decimal(str(data.get('delivery_charge', 0)))

        # Get cart items
        items = data.get('items', [])

        # Validate required fields
        if not customer_name:
            return JsonResponse({
                'success': False,
                'error': 'Customer name is required'
            }, status=400)

        if not contact_number or len(contact_number) != 10:
            return JsonResponse({
                'success': False,
                'error': 'Valid 10-digit contact number is required'
            }, status=400)

        if not location:
            return JsonResponse({
                'success': False,
                'error': 'Delivery location is required'
            }, status=400)

        if not items:
            return JsonResponse({
                'success': False,
                'error': 'Cart is empty'
            }, status=400)

        # Build shipping address
        shipping_address = f"{customer_name}\n{contact_number}\n{location}"
        if landmark:
            shipping_address += f"\nLandmark: {landmark}"

        # Calculate totals
        subtotal = Decimal('0')
        order_items_data = []

        for item in items:
            product_id = item.get('product_id')
            quantity = int(item.get('quantity', 1))

            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Product not found: {product_id}'
                }, status=400)

            # Price priority: flash_sale_price > compare_price (special price) > price (market price)
            if product.flash_sale_price:
                unit_price = product.flash_sale_price
            elif product.compare_price:
                unit_price = product.compare_price  # This is the actual selling price
            else:
                unit_price = product.price  # Fallback to market price
            item_total = unit_price * quantity
            subtotal += item_total

            order_items_data.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': item_total,
            })

        # Check if user is logged in - give 2% discount
        is_authenticated = request.user.is_authenticated
        discount_amount = Decimal('0')
        discount_percent = 0

        if is_authenticated:
            discount_percent = 2
            discount_amount = (subtotal * Decimal('2')) / Decimal('100')

        total_amount = subtotal + delivery_charge - discount_amount

        # Create the order
        order = Order.objects.create(
            user=request.user if is_authenticated else None,
            is_guest_order=not is_authenticated,
            guest_email=guest_email if not is_authenticated else None,
            status='processing',
            payment_status='pending',
            subtotal=subtotal,
            tax_amount=Decimal('0'),
            shipping_cost=delivery_charge,
            discount_amount=discount_amount,
            total_amount=total_amount,
            shipping_address=shipping_address,
            billing_address=shipping_address,
            payment_method=payment_method,
            notes=notes,
        )

        # Create order items
        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price'],
                product_name=item_data['product'].name,
                product_sku=item_data['product'].sku,
            )

        # Create order history
        order_type = "registered user" if is_authenticated else "guest"
        OrderHistory.objects.create(
            order=order,
            action='created',
            new_value='processing',
            note=f'Order placed from website by {customer_name} ({order_type})',
            created_by=request.user if is_authenticated else None,
        )

        response_data = {
            'success': True,
            'order_id': str(order.order_id),
            'order_number': order.get_order_number(),
            'message': 'Order placed successfully!',
            'is_guest': not is_authenticated,
        }

        if is_authenticated:
            response_data['discount_applied'] = f'{discount_percent}%'
            response_data['discount_amount'] = float(discount_amount)

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request data'
        }, status=400)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def check_login_status(request):
    """Check if user is logged in and eligible for discount"""
    is_authenticated = request.user.is_authenticated
    return JsonResponse({
        'is_logged_in': is_authenticated,
        'discount_percent': 2 if is_authenticated else 0,
        'username': request.user.username if is_authenticated else None,
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_user_orders(request):
    """Get orders for the current user or by contact number for guests"""
    try:
        contact_number = request.GET.get('contact', '')

        if request.user.is_authenticated:
            # Get orders for logged-in user
            orders = Order.objects.filter(user=request.user, is_deleted=False).order_by('-created_at')
        elif contact_number:
            # Get orders by contact number for guests
            orders = Order.objects.filter(
                shipping_address__contains=contact_number,
                is_guest_order=True,
                is_deleted=False
            ).order_by('-created_at')
        else:
            return JsonResponse({
                'success': False,
                'error': 'Please login or provide contact number to view orders'
            }, status=400)

        orders_data = []
        for order in orders:
            items = []
            for item in order.items.all():
                # Get product image and current price
                product_image = None
                current_price = float(item.unit_price)  # Default to stored price

                if item.product:
                    main_image = item.product.get_main_image()
                    if main_image:
                        product_image = main_image
                    # Price priority: flash_sale_price > compare_price (special price) > price (market price)
                    if item.product.flash_sale_price:
                        current_price = float(item.product.flash_sale_price)
                    elif item.product.compare_price:
                        current_price = float(item.product.compare_price)  # Actual selling price
                    else:
                        current_price = float(item.product.price)  # Market price fallback

                items.append({
                    'product_id': item.product.id if item.product else None,
                    'product_name': item.product_name,
                    'product_sku': item.product_sku if hasattr(item, 'product_sku') else '',
                    'product_image': product_image,
                    'quantity': item.quantity,
                    'unit_price': current_price,  # Use actual selling price
                    'total_price': current_price * item.quantity,
                })

            orders_data.append({
                'order_id': str(order.order_id),
                'order_number': order.get_order_number(),
                'status': order.status,
                'status_display': order.get_status_display(),
                'payment_status': order.payment_status,
                'payment_method': order.payment_method,
                'subtotal': float(order.subtotal),
                'shipping_cost': float(order.shipping_cost),
                'discount_amount': float(order.discount_amount),
                'total_amount': float(order.total_amount),
                'shipping_address': order.shipping_address,
                'notes': order.notes,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'items': items,
                'items_count': order.items.count(),
            })

        return JsonResponse({
            'success': True,
            'orders': orders_data,
            'count': len(orders_data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_order_detail(request, order_id):
    """Get detailed information about a specific order"""
    try:
        # Try to get the order
        try:
            order = Order.objects.get(order_id=order_id, is_deleted=False)
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Order not found'
            }, status=404)

        # Check if user has permission to view this order
        if request.user.is_authenticated:
            if order.user != request.user and not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have permission to view this order'
                }, status=403)
        else:
            # For guests, they need to provide contact number
            contact = request.GET.get('contact', '')
            if not contact or contact not in order.shipping_address:
                return JsonResponse({
                    'success': False,
                    'error': 'Please provide valid contact number to view this order'
                }, status=403)

        # Get order items
        items = []
        for item in order.items.all():
            # Get product image and current price
            product_image = None
            current_price = float(item.unit_price)  # Default to stored price

            if item.product:
                main_image = item.product.get_main_image()
                if main_image:
                    product_image = main_image
                # Price priority: flash_sale_price > compare_price (special price) > price (market price)
                if item.product.flash_sale_price:
                    current_price = float(item.product.flash_sale_price)
                elif item.product.compare_price:
                    current_price = float(item.product.compare_price)  # Actual selling price
                else:
                    current_price = float(item.product.price)  # Market price fallback

            items.append({
                'product_id': item.product.id if item.product else None,
                'product_name': item.product_name,
                'product_sku': item.product_sku,
                'product_image': product_image,
                'quantity': item.quantity,
                'unit_price': current_price,  # Use actual selling price
                'total_price': current_price * item.quantity,
            })

        # Get order history
        history = []
        for h in order.history.all():
            history.append({
                'action': h.get_action_display(),
                'old_value': h.old_value,
                'new_value': h.new_value,
                'note': h.note,
                'created_at': h.created_at.strftime('%Y-%m-%d %H:%M'),
            })

        order_data = {
            'order_id': str(order.order_id),
            'order_number': order.get_order_number(),
            'status': order.status,
            'status_display': order.get_status_display(),
            'payment_status': order.payment_status,
            'payment_status_display': order.get_payment_status_display(),
            'payment_method': order.payment_method,
            'subtotal': float(order.subtotal),
            'tax_amount': float(order.tax_amount),
            'shipping_cost': float(order.shipping_cost),
            'discount_amount': float(order.discount_amount),
            'total_amount': float(order.total_amount),
            'shipping_address': order.shipping_address,
            'tracking_number': order.tracking_number,
            'notes': order.notes,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': order.updated_at.strftime('%Y-%m-%d %H:%M'),
            'shipped_at': order.shipped_at.strftime('%Y-%m-%d %H:%M') if order.shipped_at else None,
            'delivered_at': order.delivered_at.strftime('%Y-%m-%d %H:%M') if order.delivered_at else None,
            'items': items,
            'history': history,
            'is_guest_order': order.is_guest_order,
        }

        return JsonResponse({
            'success': True,
            'order': order_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
