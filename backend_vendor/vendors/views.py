"""
Vendor Dashboard Views
All views for vendor's own dashboard and super admin vendor management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import Business, VendorStorefront, VendorMessage, VendorApplication
from .mixins import VendorRequiredMixin, VendorOwnerMixin, AdminRequiredMixin
from .forms import BusinessForm, StorefrontForm, VendorReplyForm
from products.models import Product, Review, Category, ProductImage
from orders.models import Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()


# ==================== VENDOR DASHBOARD VIEWS ====================

class VendorDashboardView(VendorRequiredMixin, TemplateView):
    """Vendor's main dashboard with stats - routes based on plan"""
    template_name = 'vendor/dashboard/home.html'

    def dispatch(self, request, *args, **kwargs):
        """Add cache-control headers to prevent browser caching"""
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/dashboard.html']
        return ['vendor/starter/dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()

        # Check if welcome message should be shown
        if not business.welcome_message_shown:
            context['show_welcome_message'] = True
            business.welcome_message_shown = True
            business.save(update_fields=['welcome_message_shown'])

        # Check trial status and expire if needed
        if business.subscription_status == 'trial' and not business.is_trial_active:
            business.expire_trial()

        # Basic stats
        context['total_products'] = Product.objects.filter(vendor=business, is_active=True).count()
        context['total_products_all'] = Product.objects.filter(vendor=business).count()

        # Order stats
        vendor_order_ids = OrderItem.objects.filter(vendor=business).values_list('order_id', flat=True).distinct()
        context['total_orders'] = Order.objects.filter(id__in=vendor_order_ids, is_deleted=False).count()
        context['pending_orders'] = Order.objects.filter(
            id__in=vendor_order_ids,
            status__in=['processing', 'confirmed'],
            is_deleted=False
        ).count()

        # Revenue
        paid_items = OrderItem.objects.filter(
            vendor=business,
            order__payment_status='paid'
        )
        context['total_revenue'] = paid_items.aggregate(total=Sum('total_price'))['total'] or 0

        # Reviews
        context['total_reviews'] = Review.objects.filter(product__vendor=business).count()
        context['pending_reviews'] = Review.objects.filter(
            product__vendor=business,
            status='pending'
        ).count()

        # Messages
        context['unread_messages'] = VendorMessage.objects.filter(
            business=business,
            is_read=False,
            is_from_vendor=False
        ).count()

        # Recent orders (OrderItems for this vendor)
        context['recent_orders'] = OrderItem.objects.filter(
            vendor=business,
            order__is_deleted=False
        ).select_related('order', 'order__user', 'product').order_by('-order__created_at')[:5]

        # Recent reviews (for professional plan)
        context['recent_reviews'] = Review.objects.filter(
            product__vendor=business
        ).select_related('user', 'product').order_by('-created_at')[:5]

        # Avg rating
        from django.db.models import Avg
        avg_rating = Review.objects.filter(
            product__vendor=business,
            status='approved'
        ).aggregate(avg=Avg('rating'))['avg']
        context['avg_rating'] = avg_rating or 0

        # Monthly stats
        from datetime import datetime
        now = timezone.now()
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_items = OrderItem.objects.filter(
            vendor=business,
            order__created_at__gte=first_of_month,
            order__is_deleted=False
        )
        context['monthly_orders'] = monthly_items.values('order_id').distinct().count()
        context['monthly_revenue'] = monthly_items.filter(
            order__payment_status='paid'
        ).aggregate(total=Sum('total_price'))['total'] or 0

        # Low stock products
        context['low_stock_products'] = Product.objects.filter(
            vendor=business,
            is_active=True,
            stock_quantity__lte=10
        ).order_by('stock_quantity')[:5]

        # Top products by orders
        top_product_ids = OrderItem.objects.filter(vendor=business).values('product_id').annotate(
            order_count=Count('id')
        ).order_by('-order_count')[:5]
        context['top_products'] = Product.objects.filter(
            id__in=[p['product_id'] for p in top_product_ids]
        )

        # Total customers (unique users who ordered from this vendor)
        customer_ids = Order.objects.filter(
            id__in=vendor_order_ids,
            is_deleted=False,
            user__isnull=False
        ).values_list('user_id', flat=True).distinct()
        context['total_customers'] = len(set(customer_ids))

        # Order stats for chart
        context['order_stats'] = {
            'delivered': Order.objects.filter(id__in=vendor_order_ids, status='delivered', is_deleted=False).count(),
            'processing': Order.objects.filter(id__in=vendor_order_ids, status__in=['processing', 'confirmed', 'shipped'], is_deleted=False).count(),
            'pending': Order.objects.filter(id__in=vendor_order_ids, status='pending', is_deleted=False).count(),
            'cancelled': Order.objects.filter(id__in=vendor_order_ids, status='cancelled', is_deleted=False).count(),
        }

        # Monthly revenue data for chart
        from datetime import datetime
        current_year = now.year
        monthly_data = {}
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        for i, month in enumerate(months, 1):
            month_start = datetime(current_year, i, 1, tzinfo=timezone.get_current_timezone())
            if i == 12:
                month_end = datetime(current_year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
            else:
                month_end = datetime(current_year, i + 1, 1, tzinfo=timezone.get_current_timezone())

            month_revenue = OrderItem.objects.filter(
                vendor=business,
                order__payment_status='paid',
                order__created_at__gte=month_start,
                order__created_at__lt=month_end
            ).aggregate(total=Sum('total_price'))['total'] or 0
            monthly_data[month] = float(month_revenue)

        context['monthly_data'] = monthly_data

        return context


class VendorProfileView(VendorRequiredMixin, TemplateView):
    """Vendor profile settings - edit logo and business info"""

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/profile.html']
        return ['vendor/starter/profile.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['business'] = self.get_vendor_business()
        return context

    def post(self, request, *args, **kwargs):
        """Handle profile update"""
        business = self.get_vendor_business()

        # Update business name
        business_name = request.POST.get('business_name', '').strip()
        if business_name:
            business.business_name = business_name

        # Update description
        description = request.POST.get('description', '').strip()
        business.description = description

        # Update phone
        phone = request.POST.get('phone', '').strip()
        business.phone = phone

        # Update address
        address = request.POST.get('address', '').strip()
        business.address = address

        # Handle logo upload
        if 'logo' in request.FILES:
            business.logo = request.FILES['logo']
        elif request.POST.get('remove_logo') == '1':
            business.logo = None

        business.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('vendor:profile')


class VendorPagesView(VendorRequiredMixin, TemplateView):
    """Edit About and Contact page content"""

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/pages.html']
        return ['vendor/starter/pages.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()
        context['business'] = business
        # Get or create storefront
        storefront, created = VendorStorefront.objects.get_or_create(business=business)
        context['storefront'] = storefront
        return context

    def post(self, request, *args, **kwargs):
        """Handle pages update"""
        business = self.get_vendor_business()
        storefront, created = VendorStorefront.objects.get_or_create(business=business)

        # About Page fields
        storefront.about_title = request.POST.get('about_title', '').strip()
        storefront.about_tagline = request.POST.get('about_tagline', '').strip()
        storefront.about_story = request.POST.get('about_story', '').strip()
        storefront.about_mission = request.POST.get('about_mission', '').strip()
        storefront.about_vision = request.POST.get('about_vision', '').strip()

        # Contact Page fields
        storefront.contact_address = request.POST.get('contact_address', '').strip()
        storefront.contact_city = request.POST.get('contact_city', '').strip()
        storefront.contact_phone = request.POST.get('contact_phone', '').strip()
        storefront.contact_email = request.POST.get('contact_email', '').strip()
        storefront.contact_hours = request.POST.get('contact_hours', '').strip()
        storefront.contact_hours_note = request.POST.get('contact_hours_note', '').strip()

        storefront.save()
        messages.success(request, 'Page content updated successfully!')
        return redirect('vendor:pages')


class VendorProductListView(VendorRequiredMixin, ListView):
    """List vendor's products"""
    context_object_name = 'products'
    paginate_by = 20

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/products.html']
        return ['vendor/starter/products.html']

    def get_queryset(self):
        business = self.get_vendor_business()
        queryset = Product.objects.filter(vendor=business).order_by('-created_at')

        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )

        # Filter by status
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'low_stock':
            queryset = queryset.filter(stock_quantity__lte=10)

        return queryset


class VendorProductCreateView(VendorRequiredMixin, CreateView):
    """Add new product"""
    model = Product
    fields = ['name', 'category', 'description', 'short_description', 'price', 'compare_price',
              'cost_price', 'sku', 'stock_quantity', 'low_stock_threshold',
              'is_active', 'is_featured', 'is_flash_sale', 'flash_sale_price']
    success_url = reverse_lazy('vendor:products')

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/product_form.html']
        return ['vendor/starter/product_form.html']

    def form_valid(self, form):
        form.instance.vendor = self.get_vendor_business()
        response = super().form_valid(form)

        # Handle image uploads
        images = self.request.FILES.getlist('images')
        main_image_value = self.request.POST.get('main_image', '')

        created_images = []
        for i, image in enumerate(images):
            product_image = ProductImage.objects.create(
                product=self.object,
                image=image,
                alt_text=self.object.name,
                is_main=False
            )
            created_images.append(product_image)

        # Set main image based on selection
        if main_image_value.startswith('new_'):
            try:
                index = int(main_image_value.replace('new_', ''))
                if 0 <= index < len(created_images):
                    created_images[index].is_main = True
                    created_images[index].save()
            except (ValueError, IndexError):
                # Fallback: first image is main
                if created_images:
                    created_images[0].is_main = True
                    created_images[0].save()
        elif created_images:
            # No selection, first image is main
            created_images[0].is_main = True
            created_images[0].save()

        messages.success(self.request, 'Product created successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['is_edit'] = False
        return context


class VendorProductDetailView(VendorRequiredMixin, VendorOwnerMixin, DetailView):
    """View product details"""
    model = Product
    template_name = 'vendor/products/detail.html'
    context_object_name = 'product'
    vendor_field = 'vendor'


class VendorProductUpdateView(VendorRequiredMixin, VendorOwnerMixin, UpdateView):
    """Edit product"""
    model = Product
    fields = ['name', 'category', 'description', 'short_description', 'price', 'compare_price',
              'cost_price', 'sku', 'stock_quantity', 'low_stock_threshold',
              'is_active', 'is_featured', 'is_flash_sale', 'flash_sale_price']
    vendor_field = 'vendor'

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/product_form.html']
        return ['vendor/starter/product_form.html']

    def get_success_url(self):
        return reverse_lazy('vendor:products')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Handle new image uploads
        images = self.request.FILES.getlist('images')
        main_image_value = self.request.POST.get('main_image', '')

        created_images = []
        for i, image in enumerate(images):
            product_image = ProductImage.objects.create(
                product=self.object,
                image=image,
                alt_text=self.object.name,
                is_main=False
            )
            created_images.append(product_image)

        # Handle main image selection
        if main_image_value:
            # Reset all images to not main first
            ProductImage.objects.filter(product=self.object).update(is_main=False)

            if main_image_value.startswith('existing_'):
                # Existing image selected as main
                try:
                    image_id = int(main_image_value.replace('existing_', ''))
                    ProductImage.objects.filter(id=image_id, product=self.object).update(is_main=True)
                except ValueError:
                    pass
            elif main_image_value.startswith('new_'):
                # New image selected as main
                try:
                    index = int(main_image_value.replace('new_', ''))
                    if 0 <= index < len(created_images):
                        created_images[index].is_main = True
                        created_images[index].save()
                except (ValueError, IndexError):
                    pass

        # Ensure at least one image is main
        if not ProductImage.objects.filter(product=self.object, is_main=True).exists():
            first_image = ProductImage.objects.filter(product=self.object).first()
            if first_image:
                first_image.is_main = True
                first_image.save()

        messages.success(self.request, 'Product updated successfully!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['is_edit'] = True
        context['product'] = self.object
        return context


class VendorProductDeleteView(VendorRequiredMixin, VendorOwnerMixin, DeleteView):
    """Delete product"""
    model = Product
    template_name = 'vendor/products/confirm_delete.html'
    success_url = reverse_lazy('vendor:products')
    vendor_field = 'vendor'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Product deleted successfully!')
        return super().delete(request, *args, **kwargs)


# =============================================================================
# CATEGORY MANAGEMENT
# =============================================================================

class VendorCategoryListView(VendorRequiredMixin, ListView):
    """List categories for vendor"""
    model = Category
    template_name = 'vendor/professional/categories.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()
        # Add product count for each category from this vendor
        for category in context['categories']:
            category.vendor_product_count = Product.objects.filter(
                vendor=business,
                category=category
            ).count()
        return context


class VendorCategoryCreateView(VendorRequiredMixin, CreateView):
    """Create new category"""
    model = Category
    template_name = 'vendor/professional/category_form.html'
    fields = ['name', 'icon', 'is_active']
    success_url = reverse_lazy('vendor:categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all icons already in use
        context['used_icons'] = list(Category.objects.values_list('icon', flat=True))
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)


class VendorCategoryUpdateView(VendorRequiredMixin, UpdateView):
    """Update category"""
    model = Category
    template_name = 'vendor/professional/category_form.html'
    fields = ['name', 'icon', 'is_active']
    success_url = reverse_lazy('vendor:categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get icons in use by OTHER categories (not the current one being edited)
        context['used_icons'] = list(
            Category.objects.exclude(pk=self.object.pk).values_list('icon', flat=True)
        )
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)


@login_required
def vendor_category_delete(request, pk):
    """Delete category"""
    category = get_object_or_404(Category, pk=pk)

    # Get vendor's business
    try:
        business = Business.objects.get(owner=request.user, status='approved')
    except Business.DoesNotExist:
        messages.error(request, 'You do not have an approved vendor account.')
        return redirect('vendor:categories')

    # Only check if THIS VENDOR has products in the category
    vendor_product_count = Product.objects.filter(category=category, vendor=business).count()
    if vendor_product_count > 0:
        messages.error(
            request,
            f'Cannot delete "{category.name}" because you have {vendor_product_count} products in this category. '
            f'Please reassign your products to another category first.'
        )
    else:
        category.delete()
        messages.success(request, f'Category "{category.name}" deleted successfully!')

    return redirect('vendor:categories')


class VendorFlashSaleView(VendorRequiredMixin, TemplateView):
    """Flash Sale management for vendors"""
    template_name = 'vendor/professional/flash_sale.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()

        # Get flash sale products
        context['flash_sale_products'] = Product.objects.filter(
            vendor=business,
            is_active=True,
            is_flash_sale=True
        ).order_by('-updated_at')

        # Get available products (not in flash sale)
        context['products'] = Product.objects.filter(
            vendor=business,
            is_active=True,
            is_flash_sale=False
        ).order_by('-created_at')

        return context


@login_required
def vendor_toggle_flash_sale(request, pk):
    """Toggle flash sale status for a product"""
    from .mixins import get_vendor_business
    business = get_vendor_business(request.user)
    if not business:
        messages.error(request, "You don't have vendor access.")
        return redirect('vendor:dashboard')

    product = get_object_or_404(Product, pk=pk, vendor=business)
    product.is_flash_sale = not product.is_flash_sale

    # If turning off flash sale, clear the flash price
    if not product.is_flash_sale:
        product.flash_sale_price = None

    product.save()

    if product.is_flash_sale:
        messages.success(request, f'"{product.name}" added to Flash Sale!')
    else:
        messages.success(request, f'"{product.name}" removed from Flash Sale.')

    return redirect('vendor:flash_sale')


@login_required
@require_POST
def vendor_update_flash_price(request, pk):
    """Update flash sale price for a product"""
    from .mixins import get_vendor_business
    business = get_vendor_business(request.user)
    if not business:
        messages.error(request, "You don't have vendor access.")
        return redirect('vendor:dashboard')

    product = get_object_or_404(Product, pk=pk, vendor=business)
    flash_price = request.POST.get('flash_sale_price', '')

    if flash_price:
        try:
            product.flash_sale_price = float(flash_price)
            product.save()
            messages.success(request, f'Flash sale price for "{product.name}" updated!')
        except ValueError:
            messages.error(request, 'Invalid price value.')
    else:
        product.flash_sale_price = None
        product.save()
        messages.info(request, f'Flash sale price for "{product.name}" cleared.')

    return redirect('vendor:flash_sale')


class VendorOrderListView(VendorRequiredMixin, ListView):
    """List orders containing vendor's products"""
    context_object_name = 'order_items'
    paginate_by = 20

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/orders.html']
        return ['vendor/starter/orders.html']

    def get_queryset(self):
        business = self.get_vendor_business()
        # Return order items directly for easier display
        queryset = OrderItem.objects.filter(
            vendor=business,
            order__is_deleted=False
        ).select_related('order', 'order__user', 'product').order_by('-order__created_at')

        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(order__status=status)

        return queryset


class VendorOrderDetailView(VendorRequiredMixin, DetailView):
    """View order details (only vendor's items)"""
    template_name = 'vendor/orders/detail.html'
    context_object_name = 'order'

    def get_object(self):
        business = self.get_vendor_business()
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, order_id=order_id, is_deleted=False)

        # SECURITY: Verify this order has items from this vendor
        # Prevents vendor from viewing orders that don't belong to them
        if not OrderItem.objects.filter(order=order, vendor=business).exists():
            from django.http import Http404
            raise Http404("Order not found or you don't have access to it.")

        return order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()
        order = context['order']

        # Only show vendor's items
        context['vendor_items'] = OrderItem.objects.filter(order=order, vendor=business)
        context['vendor_total'] = context['vendor_items'].aggregate(total=Sum('total_price'))['total'] or 0

        return context


class VendorReviewListView(VendorRequiredMixin, ListView):
    """List reviews for vendor's products"""
    context_object_name = 'reviews'
    paginate_by = 20

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/reviews.html']
        return ['vendor/starter/reviews.html']

    def get_queryset(self):
        business = self.get_vendor_business()
        queryset = Review.objects.filter(product__vendor=business).select_related('user', 'product').order_by('-created_at')

        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()

        # Review stats
        from django.db.models import Avg
        all_reviews = Review.objects.filter(product__vendor=business)
        context['total_reviews'] = all_reviews.count()
        context['pending_reviews'] = all_reviews.filter(status='pending').count()
        context['avg_rating'] = all_reviews.filter(status='approved').aggregate(avg=Avg('rating'))['avg'] or 0

        return context


@login_required
@require_POST
def vendor_review_respond(request, pk):
    """Respond to a review"""
    from .mixins import get_vendor_business

    business = get_vendor_business(request.user)
    if not business:
        messages.error(request, 'You must be a vendor to respond to reviews.')
        return redirect('vendor:reviews')

    try:
        review = Review.objects.get(pk=pk, product__vendor=business)
        response_text = request.POST.get('response', '').strip()

        if response_text:
            review.admin_response = response_text
            review.save()
            messages.success(request, 'Your response has been saved.')
        else:
            messages.error(request, 'Please enter a response.')

    except Review.DoesNotExist:
        messages.error(request, 'Review not found or you do not have permission to respond to it.')

    return redirect('vendor:reviews')


@login_required
@require_POST
def vendor_review_action(request, pk, action):
    """Approve or reject a review"""
    from .mixins import get_vendor_business

    business = get_vendor_business(request.user)
    if not business:
        messages.error(request, 'You must be a vendor to manage reviews.')
        return redirect('vendor:reviews')

    try:
        review = Review.objects.get(pk=pk, product__vendor=business)

        if action == 'approve':
            review.status = 'approved'
            review.save()
            messages.success(request, 'Review has been approved.')
        elif action == 'reject':
            review.status = 'rejected'
            review.save()
            messages.success(request, 'Review has been rejected.')
        else:
            messages.error(request, 'Invalid action.')

    except Review.DoesNotExist:
        messages.error(request, 'Review not found or you do not have permission to manage it.')

    return redirect('vendor:reviews')


class VendorCustomerListView(VendorRequiredMixin, ListView):
    """List customers who bought from this vendor"""
    template_name = 'vendor/customers/list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        business = self.get_vendor_business()
        order_ids = OrderItem.objects.filter(vendor=business).values_list('order_id', flat=True)
        customer_ids = Order.objects.filter(
            id__in=order_ids,
            user__isnull=False
        ).values_list('user_id', flat=True).distinct()
        return User.objects.filter(id__in=customer_ids)


class VendorCustomerDetailView(VendorRequiredMixin, DetailView):
    """View customer details and their orders from this vendor"""
    model = User
    template_name = 'vendor/customers/detail.html'
    context_object_name = 'customer'

    def get_object(self):
        """SECURITY: Only allow viewing customers who bought from this vendor"""
        business = self.get_vendor_business()
        customer = super().get_object()

        # Verify this customer has purchased from this vendor
        vendor_order_ids = OrderItem.objects.filter(vendor=business).values_list('order_id', flat=True)
        has_orders = Order.objects.filter(user=customer, id__in=vendor_order_ids).exists()

        if not has_orders:
            from django.http import Http404
            raise Http404("Customer not found or hasn't purchased from your store.")

        return customer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()
        customer = context['customer']

        # Get orders from this customer that contain vendor's items
        vendor_order_ids = OrderItem.objects.filter(vendor=business).values_list('order_id', flat=True)
        context['customer_orders'] = Order.objects.filter(
            user=customer,
            id__in=vendor_order_ids
        ).order_by('-created_at')

        return context


class VendorMessageListView(VendorRequiredMixin, ListView):
    """List messages"""
    template_name = 'vendor/messages/list.html'
    context_object_name = 'messages_list'
    paginate_by = 20

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/messages.html']
        return ['vendor/starter/messages.html']

    def get_queryset(self):
        business = self.get_vendor_business()
        # Get root messages (no parent) for this business
        queryset = VendorMessage.objects.filter(
            business=business,
            parent__isnull=True
        )

        # Filter by status if provided
        status = self.request.GET.get('status')
        if status == 'unread':
            queryset = queryset.filter(is_read=False)
        elif status == 'read':
            queryset = queryset.filter(is_read=True)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()

        # Get message stats
        all_messages = VendorMessage.objects.filter(
            business=business,
            parent__isnull=True
        )
        context['total_messages'] = all_messages.count()
        context['unread_messages'] = all_messages.filter(is_read=False).count()
        context['read_messages'] = all_messages.filter(is_read=True).count()

        return context


class VendorMessageThreadView(VendorRequiredMixin, DetailView):
    """View message thread"""
    model = VendorMessage
    template_name = 'vendor/messages/thread.html'
    context_object_name = 'message'

    def get_object(self):
        business = self.get_vendor_business()
        message = get_object_or_404(VendorMessage, pk=self.kwargs['pk'], business=business)
        # Mark as read
        if not message.is_from_vendor:
            message.mark_as_read()
        return message

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['thread'] = self.object.get_thread()
        context['reply_form'] = VendorReplyForm()
        return context


@login_required
def vendor_message_reply(request):
    """Reply to a message"""
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        reply_text = request.POST.get('message')

        try:
            business = Business.objects.get(owner=request.user, status='approved')
            parent_message = VendorMessage.objects.get(pk=message_id, business=business)

            VendorMessage.objects.create(
                business=business,
                customer=parent_message.customer,
                order=parent_message.order,
                subject=f"Re: {parent_message.subject}",
                message=reply_text,
                parent=parent_message,
                is_from_vendor=True
            )

            messages.success(request, 'Reply sent successfully!')
            return redirect('vendor:message_thread', pk=message_id)

        except (Business.DoesNotExist, VendorMessage.DoesNotExist):
            messages.error(request, 'Message not found.')
            return redirect('vendor:messages')

    return redirect('vendor:messages')


class StorefrontCustomizeView(VendorRequiredMixin, UpdateView):
    """Customize storefront appearance"""
    model = VendorStorefront
    template_name = 'vendor/storefront/customize.html'
    success_url = reverse_lazy('vendor:storefront')

    def dispatch(self, request, *args, **kwargs):
        """Add cache-control headers to prevent browser caching"""
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def get_form_class(self):
        """Return form class based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            from .forms import ProfessionalStorefrontForm
            return ProfessionalStorefrontForm
        return StorefrontForm

    def get_form_kwargs(self):
        """Pass is_professional flag to form"""
        kwargs = super().get_form_kwargs()
        business = self.get_vendor_business()
        kwargs['is_professional'] = business.plan == 'professional'
        return kwargs

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/storefront.html']
        return ['vendor/storefront/customize.html']

    def get_object(self):
        business = self.get_vendor_business()
        storefront, created = VendorStorefront.objects.get_or_create(business=business)
        return storefront

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        storefront = self.get_object()
        business = self.get_vendor_business()
        context['storefront'] = storefront
        context['is_professional'] = business.plan == 'professional'

        # Professional plan: Section ordering data for drag-drop
        if business.plan == 'professional':
            # Define available sections with metadata
            context['available_sections'] = [
                {'id': 'hero', 'name': 'Hero Banner', 'icon': 'fas fa-image', 'enabled': storefront.show_hero},
                {'id': 'categories', 'name': 'Categories', 'icon': 'fas fa-th-large', 'enabled': storefront.show_categories},
                {'id': 'featured', 'name': 'Featured Products', 'icon': 'fas fa-star', 'enabled': storefront.show_featured},
                {'id': 'new-arrivals', 'name': 'New Arrivals', 'icon': 'fas fa-clock', 'enabled': storefront.show_new_arrivals},
                {'id': 'deals', 'name': 'Flash Sales / Deals', 'icon': 'fas fa-bolt', 'enabled': storefront.show_flash_sale},
                {'id': 'newsletter', 'name': 'Newsletter', 'icon': 'fas fa-envelope', 'enabled': storefront.show_newsletter},
            ]

            # Parse current section order
            current_order = storefront.section_order.split(',') if storefront.section_order else []
            if current_order:
                # Reorder sections based on saved order
                ordered_sections = []
                for section_id in current_order:
                    for section in context['available_sections']:
                        if section['id'] == section_id:
                            ordered_sections.append(section)
                            break
                # Add any sections not in the order (newly added)
                for section in context['available_sections']:
                    if section['id'] not in current_order:
                        ordered_sections.append(section)
                context['available_sections'] = ordered_sections

            # Header style options for visual selection
            context['header_styles'] = [
                {'id': 'classic', 'name': 'Classic', 'description': 'Centered logo with horizontal navigation'},
                {'id': 'modern', 'name': 'Modern', 'description': 'Left-aligned logo with mega menu'},
                {'id': 'minimal', 'name': 'Minimal', 'description': 'Hamburger menu with slide-out navigation'},
            ]

            # Hero style options for visual selection
            context['hero_styles'] = [
                {'id': 'full_width', 'name': 'Full-Width', 'description': 'Single full-width hero image'},
                {'id': 'split', 'name': 'Split', 'description': 'Image and text side by side'},
                {'id': 'slider', 'name': 'Slider', 'description': 'Carousel with up to 3 slides'},
            ]

        return context

    def form_valid(self, form):
        messages.success(self.request, 'Storefront updated successfully!')
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        """Handle POST for both form-based, layout builder, and AJAX saves"""
        self.object = self.get_object()

        # Check for AJAX request (live preview)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.handle_ajax_save(request)

        # Check if this is a layout builder save (professional plan)
        if 'section_order' in request.POST or 'layout_template' in request.POST:
            # Handle layout builder data
            layout_template = request.POST.get('layout_template', 'classic')
            section_order = request.POST.get('section_order', '')
            sections_enabled = request.POST.get('sections_enabled', '')

            # Save layout settings to storefront
            self.object.layout_template = layout_template
            self.object.section_order = section_order
            self.object.sections_enabled = sections_enabled

            # Parse enabled sections and update show_* fields
            enabled_list = sections_enabled.split(',') if sections_enabled else []
            self.object.show_hero = 'hero' in enabled_list
            self.object.show_categories = 'categories' in enabled_list
            self.object.show_featured = 'featured' in enabled_list
            self.object.show_new_arrivals = 'new-arrivals' in enabled_list
            self.object.show_flash_sale = 'deals' in enabled_list
            self.object.show_testimonials = 'testimonials' in enabled_list
            self.object.show_newsletter = 'newsletter' in enabled_list

            # Save with explicit update_fields to ensure all changes are persisted
            self.object.save(update_fields=[
                'layout_template', 'section_order', 'sections_enabled',
                'show_hero', 'show_categories', 'show_featured',
                'show_new_arrivals', 'show_flash_sale', 'show_testimonials', 'show_newsletter'
            ])

            messages.success(request, 'Storefront layout updated successfully!')
            return redirect(self.success_url)

        # Otherwise, use standard form handling
        return super().post(request, *args, **kwargs)

    def handle_ajax_save(self, request):
        """AJAX endpoint for live preview updates"""
        import json
        from django.http import JsonResponse

        try:
            data = json.loads(request.body)
            field = data.get('field')
            value = data.get('value')

            # Whitelist of allowed fields for AJAX update
            allowed_fields = [
                'header_style', 'hero_style', 'storefront_template',
                'hero_overlay_color', 'hero_overlay_opacity',
                'primary_color', 'secondary_color', 'accent_color',
                'dashboard_primary_color', 'dashboard_sidebar_color', 'dashboard_accent_color',
                'hero_title', 'hero_subtitle', 'hero_cta_text', 'hero_cta_link',
                'hero_title_2', 'hero_subtitle_2', 'hero_cta_text_2', 'hero_cta_link_2',
                'hero_title_3', 'hero_subtitle_3', 'hero_cta_text_3', 'hero_cta_link_3',
                'show_hero', 'show_categories', 'show_featured', 'show_new_arrivals',
                'show_flash_sale', 'show_testimonials', 'show_newsletter',
                'section_order', 'sections_enabled',
            ]

            if field not in allowed_fields:
                return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)

            # Handle boolean fields
            if field.startswith('show_'):
                value = value in ['true', 'True', True, 1, '1']

            # Handle integer fields
            if field == 'hero_overlay_opacity':
                value = int(value)

            setattr(self.object, field, value)
            self.object.save(update_fields=[field])

            return JsonResponse({'success': True, 'field': field, 'value': str(value)})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def storefront_preview(request):
    """Preview storefront (redirect to public storefront)"""
    try:
        business = Business.objects.get(owner=request.user, status='approved')
        return redirect('storefront:home', vendor_slug=business.slug)
    except Business.DoesNotExist:
        messages.error(request, 'Business not found.')
        return redirect('vendor:dashboard')


@login_required
def storefront_restore(request):
    """Restore storefront to default settings"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('vendor:storefront')

    try:
        business = Business.objects.get(owner=request.user, status='approved')
        storefront = VendorStorefront.objects.get(business=business)

        # Reset all storefront settings to defaults
        storefront.primary_color = '#6366f1'
        storefront.secondary_color = '#8b5cf6'
        storefront.accent_color = '#10b981'
        storefront.header_style = 'classic'
        storefront.hero_style = 'full_width'
        storefront.hero_title = ''
        storefront.hero_subtitle = ''
        storefront.hero_cta_text = 'Shop Now'
        storefront.hero_cta_link = ''
        storefront.hero_image = ''
        storefront.hero_image_2 = ''
        storefront.hero_image_3 = ''
        storefront.hero_title_2 = ''
        storefront.hero_subtitle_2 = ''
        storefront.hero_cta_text_2 = ''
        storefront.hero_cta_link_2 = ''
        storefront.hero_title_3 = ''
        storefront.hero_subtitle_3 = ''
        storefront.hero_cta_text_3 = ''
        storefront.hero_cta_link_3 = ''
        storefront.hero_overlay_color = '#000000'
        storefront.hero_overlay_opacity = 30
        storefront.layout_template = 'classic'
        storefront.section_order = 'hero,categories,featured,deals,new-arrivals,testimonials,newsletter'
        storefront.show_hero = True
        storefront.show_categories = True
        storefront.show_featured = True
        storefront.show_flash_sale = True
        storefront.show_new_arrivals = True
        storefront.show_testimonials = False
        storefront.show_newsletter = True
        storefront.dashboard_primary_color = '#6366f1'
        storefront.dashboard_sidebar_color = '#111827'
        storefront.dashboard_accent_color = '#10b981'

        storefront.save()

        messages.success(request, 'Storefront settings restored to default successfully!')
    except Business.DoesNotExist:
        messages.error(request, 'Business not found.')
    except VendorStorefront.DoesNotExist:
        messages.error(request, 'Storefront settings not found.')
    except Exception as e:
        messages.error(request, f'Error restoring settings: {str(e)}')

    return redirect('vendor:storefront')


class VendorAnalyticsView(VendorRequiredMixin, TemplateView):
    """Vendor analytics dashboard"""
    template_name = 'vendor/analytics/home.html'

    def get_template_names(self):
        """Return template based on vendor's plan"""
        business = self.get_vendor_business()
        if business.plan == 'professional':
            return ['vendor/professional/analytics.html']
        return ['vendor/starter/analytics.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()
        from datetime import timedelta
        from django.db.models import Avg

        # Get date range from query params (default 30 days)
        days = int(self.request.GET.get('days', 30))
        period_start = timezone.now() - timedelta(days=days)
        previous_period_start = period_start - timedelta(days=days)

        # Current period order items
        current_items = OrderItem.objects.filter(
            vendor=business,
            order__created_at__gte=period_start,
            order__is_deleted=False
        )

        # Previous period order items (for comparison)
        previous_items = OrderItem.objects.filter(
            vendor=business,
            order__created_at__gte=previous_period_start,
            order__created_at__lt=period_start,
            order__is_deleted=False
        )

        # Revenue calculations
        current_revenue = current_items.filter(
            order__payment_status='paid'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        previous_revenue = previous_items.filter(
            order__payment_status='paid'
        ).aggregate(total=Sum('total_price'))['total'] or 0

        context['total_revenue'] = current_revenue
        if previous_revenue > 0:
            context['revenue_change'] = ((current_revenue - previous_revenue) / previous_revenue) * 100
        else:
            context['revenue_change'] = None

        # Orders calculations
        current_orders = current_items.values('order_id').distinct().count()
        previous_orders = previous_items.values('order_id').distinct().count()

        context['total_orders'] = current_orders
        if previous_orders > 0:
            context['orders_change'] = ((current_orders - previous_orders) / previous_orders) * 100
        else:
            context['orders_change'] = None

        # Average order value
        if current_orders > 0:
            context['avg_order_value'] = current_revenue / current_orders
            previous_aov = previous_revenue / previous_orders if previous_orders > 0 else 0
            if previous_aov > 0:
                context['aov_change'] = ((context['avg_order_value'] - previous_aov) / previous_aov) * 100
            else:
                context['aov_change'] = None
        else:
            context['avg_order_value'] = 0
            context['aov_change'] = None

        # Conversion rate (placeholder - would need view tracking)
        context['conversion_rate'] = 0
        context['conversion_change'] = None

        # Categories with product counts
        from products.models import Category
        context['categories'] = Category.objects.filter(
            products__vendor=business,
            products__is_active=True
        ).annotate(product_count=Count('products')).distinct()

        # Top products by order count
        top_product_ids = OrderItem.objects.filter(
            vendor=business
        ).values('product_id').annotate(
            order_count=Count('id')
        ).order_by('-order_count')[:5]

        # Create a dict for order counts
        product_order_counts = {p['product_id']: p['order_count'] for p in top_product_ids}

        # Get products and add order_count attribute
        top_products = list(Product.objects.filter(
            id__in=[p['product_id'] for p in top_product_ids]
        ).select_related('category'))

        for product in top_products:
            product.order_count = product_order_counts.get(product.id, 0)

        # Sort by order count
        top_products.sort(key=lambda x: x.order_count, reverse=True)
        context['top_products'] = top_products

        # Traffic sources (placeholder - would need analytics integration)
        context['traffic_sources'] = []

        return context


class VendorUpgradeView(VendorRequiredMixin, TemplateView):
    """Upgrade page for vendors to choose paid plans"""
    template_name = 'vendor/upgrade.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_vendor_business()
        context['current_plan'] = business.plan
        context['subscription_status'] = business.subscription_status
        context['trial_days_remaining'] = business.trial_days_remaining
        context['is_trial_active'] = business.is_trial_active
        return context


# ==================== SUPER ADMIN VENDOR MANAGEMENT ====================

class AdminVendorListView(AdminRequiredMixin, ListView):
    """List all registered businesses"""
    model = Business
    template_name = 'admin/vendors/list.html'
    context_object_name = 'businesses'
    paginate_by = 20

    def get_queryset(self):
        queryset = Business.objects.all().order_by('-created_at')

        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(business_name__icontains=search) |
                Q(email__icontains=search)
            )

        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_vendors'] = Business.objects.count()
        context['approved_vendors'] = Business.objects.filter(status='approved').count()
        context['pending_vendors'] = Business.objects.filter(status='pending').count()
        context['suspended_vendors'] = Business.objects.filter(status='suspended').count()

        # Add real-time stats for each vendor
        vendors_with_stats = []
        for vendor in context['businesses']:
            # Get product count
            product_count = Product.objects.filter(vendor=vendor).count()

            # Get order count
            vendor_order_ids = OrderItem.objects.filter(vendor=vendor).values_list('order_id', flat=True)
            order_count = Order.objects.filter(id__in=vendor_order_ids).count()

            # Get revenue
            paid_items = OrderItem.objects.filter(vendor=vendor, order__payment_status='paid')
            revenue = paid_items.aggregate(total=Sum('total_price'))['total'] or 0

            vendors_with_stats.append({
                'vendor': vendor,
                'product_count': product_count,
                'order_count': order_count,
                'revenue': revenue,
            })

        context['vendors_with_stats'] = vendors_with_stats
        return context


class AdminVendorAddView(AdminRequiredMixin, CreateView):
    """Add new business"""
    model = Business
    form_class = BusinessForm
    template_name = 'admin/vendors/form.html'
    success_url = reverse_lazy('vendor_admin:list')

    def form_valid(self, form):
        form.instance.approved_by = self.request.user
        messages.success(self.request, f'Business "{form.instance.business_name}" added successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context


class AdminVendorDetailView(AdminRequiredMixin, DetailView):
    """View business details"""
    model = Business
    template_name = 'admin/vendors/detail.html'
    context_object_name = 'vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = context['vendor']

        # Stats
        total_products = Product.objects.filter(vendor=business).count()
        active_products = Product.objects.filter(vendor=business, is_active=True).count()

        vendor_order_ids = OrderItem.objects.filter(vendor=business).values_list('order_id', flat=True)
        total_orders = Order.objects.filter(id__in=vendor_order_ids).count()

        paid_items = OrderItem.objects.filter(vendor=business, order__payment_status='paid')
        total_revenue = paid_items.aggregate(total=Sum('total_price'))['total'] or 0

        # Commission
        commission_earned = total_revenue * (business.commission_rate / 100)

        # Add stats dict for template
        context['stats'] = {
            'total_products': total_products,
            'active_products': active_products,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'commission_earned': commission_earned,
        }

        # Recent orders
        context['recent_orders'] = Order.objects.filter(
            id__in=vendor_order_ids
        ).order_by('-created_at')[:5]

        return context


class AdminVendorEditView(AdminRequiredMixin, UpdateView):
    """Edit business"""
    model = Business
    form_class = BusinessForm
    template_name = 'admin/vendors/form.html'

    def get_success_url(self):
        return reverse_lazy('vendor_admin:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Business updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class AdminVendorDeleteView(AdminRequiredMixin, DeleteView):
    """Delete business"""
    model = Business
    template_name = 'admin/vendors/confirm_delete.html'
    success_url = reverse_lazy('vendor_admin:list')

    def delete(self, request, *args, **kwargs):
        business = self.get_object()
        messages.success(request, f'Business "{business.business_name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def vendor_approve(request, pk):
    """Approve a business"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    business = get_object_or_404(Business, pk=pk)
    business.status = 'approved'
    business.approved_by = request.user
    business.approved_at = timezone.now()
    business.save()

    messages.success(request, f'Business "{business.business_name}" approved!')
    return redirect('vendor_admin:detail', pk=pk)


@login_required
def vendor_suspend(request, pk):
    """Suspend a business"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    business = get_object_or_404(Business, pk=pk)
    business.status = 'suspended'
    business.save()

    messages.success(request, f'Business "{business.business_name}" suspended!')
    return redirect('vendor_admin:detail', pk=pk)


@login_required
def vendor_reject(request, pk):
    """Reject a business"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    business = get_object_or_404(Business, pk=pk)
    business.status = 'rejected'
    business.save()

    messages.success(request, f'Business "{business.business_name}" rejected!')
    return redirect('vendor_admin:detail', pk=pk)


@login_required
def vendor_stats_api(request, pk):
    """Get vendor stats as JSON"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    business = get_object_or_404(Business, pk=pk)

    vendor_order_ids = OrderItem.objects.filter(vendor=business).values_list('order_id', flat=True)
    paid_items = OrderItem.objects.filter(vendor=business, order__payment_status='paid')

    stats = {
        'total_products': Product.objects.filter(vendor=business).count(),
        'active_products': Product.objects.filter(vendor=business, is_active=True).count(),
        'total_orders': Order.objects.filter(id__in=vendor_order_ids).count(),
        'total_revenue': float(paid_items.aggregate(total=Sum('total_price'))['total'] or 0),
        'commission_rate': float(business.commission_rate),
    }

    return JsonResponse({'success': True, 'stats': stats})


# ==================== VENDOR APPLICATION MANAGEMENT ====================

class AdminApplicationListView(AdminRequiredMixin, ListView):
    """List all vendor applications"""
    model = VendorApplication
    template_name = 'admin/vendors/applications/list.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self):
        queryset = VendorApplication.objects.all().order_by('-submitted_at')

        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(business_name__icontains=search) |
                Q(business_email__icontains=search) |
                Q(user__username__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_applications'] = VendorApplication.objects.count()
        context['pending_applications'] = VendorApplication.objects.filter(status='pending').count()
        context['approved_applications'] = VendorApplication.objects.filter(status='approved').count()
        context['rejected_applications'] = VendorApplication.objects.filter(status='rejected').count()
        return context


class AdminApplicationDetailView(AdminRequiredMixin, DetailView):
    """View application details"""
    model = VendorApplication
    template_name = 'admin/vendors/applications/detail.html'
    context_object_name = 'application'


@login_required
def application_approve(request, pk):
    """Approve a vendor application and create business"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    application = get_object_or_404(VendorApplication, pk=pk)

    if application.status == 'approved':
        messages.warning(request, 'Application already approved!')
        return redirect('vendor_admin:application_detail', pk=pk)

    # Create the business
    from django.utils.text import slugify
    slug = slugify(application.business_name)
    # Ensure unique slug
    base_slug = slug
    counter = 1
    while Business.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Calculate trial end date
    from datetime import timedelta
    trial_end = timezone.now() + timedelta(days=14)

    business = Business.objects.create(
        email=application.business_email,
        business_name=application.business_name,
        slug=slug,
        description=application.description,
        owner=application.user,
        status='approved',
        approved_at=timezone.now(),
        approved_by=request.user,
        phone=application.phone,
        address=application.address,
        # Trial subscription fields
        plan=getattr(application, 'selected_plan', 'starter'),
        subscription_status='trial',
        trial_start_date=timezone.now(),
        trial_end_date=trial_end,
    )

    # Update application
    application.status = 'approved'
    application.reviewed_by = request.user
    application.reviewed_at = timezone.now()
    application.created_business = business
    application.save()

    messages.success(request, f'Application approved! Business "{business.business_name}" created.')
    return redirect('vendor_admin:applications')


@login_required
def application_reject(request, pk):
    """Reject a vendor application"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    application = get_object_or_404(VendorApplication, pk=pk)

    if application.status == 'rejected':
        messages.warning(request, 'Application already rejected!')
        return redirect('vendor_admin:application_detail', pk=pk)

    reason = request.POST.get('reason', 'Your application did not meet our requirements.')

    application.status = 'rejected'
    application.rejection_reason = reason
    application.reviewed_by = request.user
    application.reviewed_at = timezone.now()
    application.save()

    messages.success(request, f'Application from "{application.business_name}" rejected.')
    return redirect('vendor_admin:applications')


# ======================
# Admin Subscription Management
# ======================

@login_required
@require_POST
def admin_extend_trial(request, pk):
    """Extend a vendor's trial period"""
    if not request.user.is_staff:
        messages.error(request, 'Permission denied')
        return redirect('vendor_admin:detail', pk=pk)

    business = get_object_or_404(Business, pk=pk)
    days = int(request.POST.get('days', 7))

    if days < 1 or days > 90:
        messages.error(request, 'Days must be between 1 and 90')
        return redirect('vendor_admin:detail', pk=pk)

    from datetime import timedelta

    # Extend from current end date or from now if expired
    if business.trial_end_date and business.trial_end_date > timezone.now():
        business.trial_end_date = business.trial_end_date + timedelta(days=days)
    else:
        business.trial_end_date = timezone.now() + timedelta(days=days)

    # Reset status to trial if expired
    if business.subscription_status == 'expired':
        business.subscription_status = 'trial'
        business.trial_expiry_email_sent = False

    business.save(update_fields=['trial_end_date', 'subscription_status', 'trial_expiry_email_sent'])

    messages.success(request, f'Trial extended by {days} days for "{business.business_name}"')
    return redirect('vendor_admin:detail', pk=pk)


@login_required
@require_POST
def admin_change_plan(request, pk):
    """Change a vendor's plan"""
    if not request.user.is_staff:
        messages.error(request, 'Permission denied')
        return redirect('vendor_admin:detail', pk=pk)

    business = get_object_or_404(Business, pk=pk)
    plan = request.POST.get('plan', 'starter')

    if plan not in ['starter', 'professional']:
        messages.error(request, 'Invalid plan selected')
        return redirect('vendor_admin:detail', pk=pk)

    old_plan = business.get_plan_display()
    business.plan = plan
    business.save(update_fields=['plan'])

    # Store vendor_id in admin session for easy impersonation
    request.session['admin_vendor_id'] = pk

    new_plan = business.get_plan_display()
    messages.success(
        request,
        f'Plan changed from {old_plan} to {new_plan} for "{business.business_name}". '
        f'The vendor will see their new {new_plan} dashboard immediately on refresh.'
    )
    return redirect('vendor_admin:detail', pk=pk)


@login_required
@require_POST
def admin_activate_subscription(request, pk):
    """Manually activate a vendor's subscription"""
    if not request.user.is_staff:
        messages.error(request, 'Permission denied')
        return redirect('vendor_admin:detail', pk=pk)

    business = get_object_or_404(Business, pk=pk)

    business.subscription_status = 'active'
    business.save(update_fields=['subscription_status'])

    messages.success(request, f'Subscription activated for "{business.business_name}"')
    return redirect('vendor_admin:detail', pk=pk)


@login_required
@require_POST
def admin_cancel_trial(request, pk):
    """Cancel/expire a vendor's trial immediately"""
    if not request.user.is_staff:
        messages.error(request, 'Permission denied')
        return redirect('vendor_admin:detail', pk=pk)

    business = get_object_or_404(Business, pk=pk)

    if business.subscription_status not in ['trial', 'active']:
        messages.warning(request, 'Trial is already cancelled or expired')
        return redirect('vendor_admin:detail', pk=pk)

    business.subscription_status = 'expired'
    business.trial_end_date = timezone.now()
    business.save(update_fields=['subscription_status', 'trial_end_date'])

    messages.success(request, f'Trial cancelled for "{business.business_name}"')
    return redirect('vendor_admin:detail', pk=pk)
