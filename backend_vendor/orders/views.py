from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Order, OrderItem, ShippingMethod, OrderHistory
from .forms import OrderUpdateForm
from ecommerce.mixins import AdminRequiredMixin
from products.models import Product

User = get_user_model()


class OrderListView(AdminRequiredMixin, ListView):
    model = Order
    template_name = 'admin/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        try:
            # Get all non-deleted orders
            all_orders = list(Order.objects.filter(is_deleted=False))

            # Get filter parameters
            search = self.request.GET.get('search', '').strip().lower()
            status = self.request.GET.get('status', '')
            payment_status = self.request.GET.get('payment_status', '')

            # Search by order ID or customer email/name
            if search:
                all_orders = [
                    order for order in all_orders
                    if search in str(order.order_id).lower()
                    or search in order.user.email.lower()
                    or search in (order.user.get_full_name() or '').lower()
                    or search in order.get_order_number().lower()
                ]

            # Filter by status
            if status:
                all_orders = [order for order in all_orders if order.status == status]

            # Filter by payment status
            if payment_status:
                all_orders = [order for order in all_orders if order.payment_status == payment_status]

            # Sort by created_at descending (newest first)
            all_orders.sort(key=lambda x: x.created_at, reverse=True)

            return all_orders
        except Exception as e:
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_payment_status'] = self.request.GET.get('payment_status', '')
        context['status_choices'] = Order.STATUS_CHOICES
        context['payment_status_choices'] = Order.PAYMENT_STATUS_CHOICES

        # Calculate stats from non-deleted orders
        try:
            all_orders = list(Order.objects.filter(is_deleted=False))
            context['total_orders'] = len(all_orders)
            context['pending_orders'] = sum(1 for o in all_orders if o.status == 'pending')
            context['processing_orders'] = sum(1 for o in all_orders if o.status in ['confirmed', 'processing', 'shipped'])
            context['completed_orders'] = sum(1 for o in all_orders if o.status == 'delivered')
        except:
            context['total_orders'] = 0
            context['pending_orders'] = 0
            context['processing_orders'] = 0
            context['completed_orders'] = 0

        return context


class DeletedOrderListView(AdminRequiredMixin, ListView):
    """View for showing deleted orders with restore option"""
    model = Order
    template_name = 'admin/orders/deleted.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        try:
            # Get all deleted orders
            all_orders = list(Order.objects.filter(is_deleted=True))

            # Get search parameter
            search = self.request.GET.get('search', '').strip().lower()

            # Search by order ID or customer email/name
            if search:
                all_orders = [
                    order for order in all_orders
                    if search in str(order.order_id).lower()
                    or search in order.user.email.lower()
                    or search in (order.user.get_full_name() or '').lower()
                    or search in order.get_order_number().lower()
                ]

            # Sort by deleted_at descending (most recently deleted first)
            all_orders.sort(key=lambda x: x.deleted_at or x.created_at, reverse=True)

            return all_orders
        except Exception as e:
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')

        # Count deleted orders
        try:
            context['deleted_count'] = Order.objects.filter(is_deleted=True).count()
        except:
            context['deleted_count'] = 0

        return context


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def quick_update_order(request):
    """Quick update order status or payment status from list view"""
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        field = request.POST.get('field')
        value = request.POST.get('value')

        try:
            order = Order.objects.get(order_id=order_id)

            if field == 'status':
                old_status = order.status
                old_display = order.get_status_display()
                order.status = value
                # Update timestamps
                if value == 'shipped' and not order.shipped_at:
                    order.shipped_at = timezone.now()
                elif value == 'delivered' and not order.delivered_at:
                    order.delivered_at = timezone.now()
                order.save()

                # Save history
                OrderHistory.objects.create(
                    order=order,
                    action='status_changed',
                    old_value=old_display,
                    new_value=order.get_status_display(),
                    created_by=request.user
                )

                # Get badge class
                badge_class = 'primary'
                if value == 'delivered':
                    badge_class = 'success'
                elif value in ['processing', 'confirmed']:
                    badge_class = 'warning'
                elif value in ['cancelled', 'returned']:
                    badge_class = 'danger'

                return JsonResponse({
                    'success': True,
                    'display': order.get_status_display(),
                    'badge_class': badge_class
                })

            elif field == 'payment_status':
                old_payment = 'Paid' if order.payment_status == 'paid' else 'Unpaid'
                order.payment_status = value
                order.save()

                # Get badge class and display text
                if value == 'paid':
                    badge_class = 'success'
                    display_text = 'Paid'
                else:
                    badge_class = 'warning'
                    display_text = 'Unpaid'

                # Save history
                OrderHistory.objects.create(
                    order=order,
                    action='payment_changed',
                    old_value=old_payment,
                    new_value=display_text,
                    created_by=request.user
                )

                return JsonResponse({
                    'success': True,
                    'display': display_text,
                    'badge_class': badge_class
                })

        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def soft_delete_order(request, order_id):
    """Soft delete an order"""
    if request.method == 'POST':
        order = get_object_or_404(Order, order_id=order_id)

        order.is_deleted = True
        order.deleted_at = timezone.now()
        order.save()

        return JsonResponse({
            'success': True,
            'message': f'Order {order.get_order_number()} has been moved to trash'
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def restore_order(request, order_id):
    """Restore a soft-deleted order"""
    if request.method == 'POST':
        order = get_object_or_404(Order, order_id=order_id, is_deleted=True)

        order.is_deleted = False
        order.deleted_at = None
        order.save()

        return JsonResponse({
            'success': True,
            'message': f'Order {order.get_order_number()} has been restored'
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def permanent_delete_order(request, order_id):
    """Permanently delete an order - only superusers"""
    if request.method == 'POST':
        order = get_object_or_404(Order, order_id=order_id, is_deleted=True)

        order_number = order.get_order_number()
        order.delete()

        return JsonResponse({
            'success': True,
            'message': f'Order {order_number} has been permanently deleted'
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


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
            context['order_history'] = self.object.history.all()[:20]
        except:
            context['order_items'] = []
            context['order_history'] = []
        return context


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def update_order(request, order_id):
    """Update an existing order with full editing capability"""
    order = get_object_or_404(Order, order_id=order_id)
    order_items = list(order.items.all())

    # Parse shipping address to extract customer details
    address_lines = order.shipping_address.split('\n') if order.shipping_address else []
    customer_name = address_lines[0] if len(address_lines) > 0 else ''
    contact_number = address_lines[1] if len(address_lines) > 1 else ''
    location_line = address_lines[2] if len(address_lines) > 2 else ''

    # Extract landmark if present
    landmark = ''
    for line in address_lines[3:]:
        if line.startswith('Landmark:'):
            landmark = line.replace('Landmark:', '').strip()
            break
        elif not landmark:
            landmark = line.strip()

    if request.method == 'POST':
        try:
            # Get customer details
            new_customer_name = request.POST.get('customer_name', '').strip()
            new_contact_number = request.POST.get('contact_number', '').strip()
            new_location = request.POST.get('location', '').strip()
            new_landmark = request.POST.get('landmark', '').strip()

            if not new_customer_name or not new_contact_number or not new_location:
                messages.error(request, 'Please fill in all required customer details.')
                return redirect('orders:update', order_id=order_id)

            # Build shipping address
            shipping_address = f"{new_customer_name}\n{new_contact_number}\n{new_location}"
            if new_landmark:
                shipping_address += f"\nLandmark: {new_landmark}"

            # Get order details
            status = request.POST.get('status', order.status)
            payment_status = request.POST.get('payment_status', order.payment_status)
            payment_method = request.POST.get('payment_method', order.payment_method)
            shipping_method = request.POST.get('shipping_method', '')
            tracking_number = request.POST.get('tracking_number', '')
            notes = request.POST.get('notes', '')
            delivery_charge = Decimal(request.POST.get('delivery_charge', '0') or '0')

            # Get products
            product_ids = request.POST.getlist('products')
            quantities = request.POST.getlist('quantities')
            prices = request.POST.getlist('prices')

            if not product_ids or not any(product_ids):
                messages.error(request, 'Please add at least one product to the order.')
                return redirect('orders:update', order_id=order_id)

            # Calculate totals
            subtotal = Decimal('0.00')
            new_items_data = []

            for i, product_id in enumerate(product_ids):
                if product_id:
                    product = get_object_or_404(Product, id=product_id)
                    quantity = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
                    unit_price = Decimal(prices[i]) if i < len(prices) and prices[i] else product.price
                    item_total = unit_price * quantity
                    subtotal += item_total
                    new_items_data.append({
                        'product': product,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_price': item_total
                    })

            total_amount = subtotal + delivery_charge

            # Update order
            old_status = order.status
            order.status = status
            order.payment_status = payment_status
            order.payment_method = payment_method
            order.shipping_method = shipping_method
            order.tracking_number = tracking_number
            order.notes = notes
            order.shipping_address = shipping_address
            order.billing_address = shipping_address
            order.subtotal = subtotal
            order.shipping_cost = delivery_charge
            order.total_amount = total_amount

            # Update timestamps based on status changes
            if status != old_status:
                if status == 'shipped' and not order.shipped_at:
                    order.shipped_at = timezone.now()
                elif status == 'delivered' and not order.delivered_at:
                    order.delivered_at = timezone.now()

            order.save()

            # Delete old items and create new ones
            order.items.all().delete()
            for item_data in new_items_data:
                OrderItem.objects.create(
                    order=order,
                    product=item_data['product'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['total_price'],
                    product_name=item_data['product'].name,
                    product_sku=item_data['product'].sku
                )

            messages.success(request, f'Order #{order.get_order_number()} updated successfully!')
            return redirect('orders:detail', order_id=order.order_id)

        except Exception as e:
            messages.error(request, f'Error updating order: {str(e)}')
            return redirect('orders:update', order_id=order_id)

    # GET request - show form
    from .delivery_rates import get_all_locations
    context = {
        'order': order,
        'order_items': order_items,
        'products': list(Product.objects.filter(is_active=True)),
        'delivery_locations': get_all_locations(),
        'customer_name': customer_name,
        'contact_number': contact_number,
        'current_location': location_line,
        'landmark': landmark,
    }
    return render(request, 'admin/orders/update.html', context)


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


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def create_order(request):
    """Create a new order from admin panel"""
    if request.method == 'POST':
        try:
            # Get customer details (manual entry)
            customer_name = request.POST.get('customer_name', '').strip()
            contact_number = request.POST.get('contact_number', '').strip()
            location = request.POST.get('location', '').strip()
            landmark = request.POST.get('landmark', '').strip()

            if not customer_name or not contact_number or not location:
                messages.error(request, 'Please fill in all required customer details.')
                return redirect('orders:create')

            # Build shipping address from customer details
            shipping_address = f"{customer_name}\n{contact_number}\n{location}"
            if landmark:
                shipping_address += f"\nLandmark: {landmark}"

            # Get payment and delivery details
            payment_method = request.POST.get('payment_method', 'cod')
            delivery_charge = Decimal(request.POST.get('delivery_charge', '0') or '0')
            notes = request.POST.get('notes', '')

            # Get products, quantities, and custom prices
            product_ids = request.POST.getlist('products')
            quantities = request.POST.getlist('quantities')
            prices = request.POST.getlist('prices')

            if not product_ids or not any(product_ids):
                messages.error(request, 'Please add at least one product to the order.')
                return redirect('orders:create')

            # Calculate totals
            subtotal = Decimal('0.00')
            order_items_data = []

            for i, product_id in enumerate(product_ids):
                if product_id:
                    product = get_object_or_404(Product, id=product_id)
                    quantity = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
                    # Use custom price if provided, otherwise use product price
                    unit_price = Decimal(prices[i]) if i < len(prices) and prices[i] else product.price
                    item_total = unit_price * quantity
                    subtotal += item_total
                    order_items_data.append({
                        'product': product,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_price': item_total
                    })

            # Calculate total (no tax for manual orders)
            total_amount = subtotal + delivery_charge

            # Use admin user as the order user (for manual orders)
            order = Order.objects.create(
                user=request.user,
                status='processing',
                payment_status='pending' if payment_method == 'cod' else 'paid',
                subtotal=subtotal,
                tax_amount=Decimal('0.00'),
                shipping_cost=delivery_charge,
                discount_amount=Decimal('0.00'),
                total_amount=total_amount,
                shipping_address=shipping_address,
                billing_address=shipping_address,
                shipping_method='Standard Delivery',
                payment_method=payment_method,
                notes=notes
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
                    product_sku=item_data['product'].sku
                )

            # Create order history entry
            OrderHistory.objects.create(
                order=order,
                action='created',
                new_value='Processing',
                created_by=request.user
            )

            messages.success(request, f'Order #{order.get_order_number()} created successfully!')
            return redirect('orders:detail', order_id=order.order_id)

        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            return redirect('orders:create')

    # GET request - show form
    from .delivery_rates import get_all_locations
    context = {
        'products': list(Product.objects.filter(is_active=True)),
        'delivery_locations': get_all_locations(),
    }
    return render(request, 'admin/orders/create.html', context)