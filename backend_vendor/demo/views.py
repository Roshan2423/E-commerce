from django.shortcuts import render
from django.http import Http404
from products.models import Category as RealCategory
from datetime import datetime

# Import DemoSettings - with fallback if migrations haven't run
try:
    from .models import DemoSettings
    DEMO_SETTINGS_AVAILABLE = True
except Exception:
    DEMO_SETTINGS_AVAILABLE = False


def get_demo_products():
    """
    Get products for demo pages.
    Returns admin-selected products if available, otherwise falls back to static data.
    """
    if DEMO_SETTINGS_AVAILABLE:
        try:
            settings = DemoSettings.get_settings()
            # Get all selected products (filter is_active in Python due to Djongo bug)
            all_products = list(settings.all_products.all())
            all_products = [p for p in all_products if p.is_active][:12]
            if all_products:
                return all_products
        except Exception as e:
            print(f"[Demo] Error getting products: {e}")
    return DEMO_PRODUCTS


def get_demo_categories():
    """
    Get categories for demo pages.
    Returns admin-selected categories if available, otherwise falls back to static data.
    """
    if DEMO_SETTINGS_AVAILABLE:
        try:
            settings = DemoSettings.get_settings()
            categories = list(settings.categories.all())
            if categories:
                return categories
        except Exception as e:
            print(f"[Demo] Error getting categories: {e}")
    return DEMO_CATEGORIES


def get_featured_products():
    """Get featured products for demo - admin selected or fallback"""
    if DEMO_SETTINGS_AVAILABLE:
        try:
            settings = DemoSettings.get_settings()
            # Get all selected products (filter is_active in Python due to Djongo bug)
            products = list(settings.featured_products.all())
            products = [p for p in products if p.is_active][:8]
            if products:
                return products
        except Exception as e:
            print(f"[Demo] Error getting featured products: {e}")
    return [p for p in DEMO_PRODUCTS if p.is_featured][:8]


def get_flash_sale_products():
    """Get flash sale products for demo - admin selected or fallback"""
    if DEMO_SETTINGS_AVAILABLE:
        try:
            settings = DemoSettings.get_settings()
            # Get all selected products (filter is_active in Python due to Djongo bug)
            products = list(settings.flash_sale_products.all())
            products = [p for p in products if p.is_active][:8]
            if products:
                return products
        except Exception as e:
            print(f"[Demo] Error getting flash sale products: {e}")
    return [p for p in DEMO_PRODUCTS if p.is_flash_sale][:8]


def get_new_arrival_products():
    """Get new arrivals for demo - admin selected or fallback"""
    if DEMO_SETTINGS_AVAILABLE:
        try:
            settings = DemoSettings.get_settings()
            # Get all selected products (filter is_active in Python due to Djongo bug)
            products = list(settings.new_arrival_products.all())
            products = [p for p in products if p.is_active][:8]
            if products:
                return products
        except Exception as e:
            print(f"[Demo] Error getting new arrival products: {e}")
    return DEMO_PRODUCTS[:8]


# ============== STATIC DEMO DATA (FALLBACK) ==============
# This data is used for demo pages when admin hasn't selected products

class DemoCategory:
    def __init__(self, id, name, slug):
        self.id = id
        self.name = name
        self.slug = slug

class DemoProduct:
    def __init__(self, id, name, price, compare_price=None, category=None,
                 is_featured=False, is_flash_sale=False, stock_quantity=100,
                 description="Sample product description", sku=None, is_active=True):
        self.id = id
        self.name = name
        self.price = price
        self.compare_price = compare_price
        self.category = category
        self.is_featured = is_featured
        self.is_flash_sale = is_flash_sale
        self.stock_quantity = stock_quantity
        self.description = description
        self.sku = sku or f"DEMO-{id:04d}"
        self.is_active = is_active

    def get_main_image(self):
        return None  # Demo products have no images

    def get_discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

class DemoReview:
    def __init__(self, id, rating, comment, user_name, created_at="2024-01-15"):
        self.id = id
        self.rating = rating
        self.comment = comment
        self.user_name = user_name
        self.created_at = created_at
        self.status = 'approved'

class DemoOrder:
    def __init__(self, id, order_number, total_amount, status, created_at, customer_name, email=None):
        self.id = id
        self.order_number = order_number
        self.total_amount = total_amount
        self.status = status
        # Parse date string to datetime object
        if isinstance(created_at, str):
            self.created_at = datetime.strptime(created_at, "%Y-%m-%d")
        else:
            self.created_at = created_at
        self.customer_name = customer_name
        self.payment_status = 'paid' if status in ['delivered', 'shipped'] else 'unpaid'
        # Generate email from customer name if not provided
        if email:
            self.email = email
        else:
            name_part = customer_name.split()[0].lower() if customer_name else 'guest'
            self.email = f'{name_part}@example.com'

class DemoCustomer:
    def __init__(self, id, username, email, date_joined):
        self.id = id
        self.username = username
        self.email = email
        # Parse date string to datetime object
        if isinstance(date_joined, str):
            self.date_joined = datetime.strptime(date_joined, "%Y-%m-%d")
        else:
            self.date_joined = date_joined
        self.is_staff = False

    def get_full_name(self):
        return self.username

class DemoMessage:
    def __init__(self, id, name, email, subject, message, status, created_at):
        self.id = id
        self.name = name
        self.email = email
        self.subject = subject
        self.message = message
        self.status = status
        self.created_at = created_at


# Create static categories
DEMO_CATEGORIES = [
    DemoCategory(1, 'Electronics', 'electronics'),
    DemoCategory(2, 'Fashion', 'fashion'),
    DemoCategory(3, 'Home & Garden', 'home-garden'),
    DemoCategory(4, 'Sports', 'sports'),
    DemoCategory(5, 'Books', 'books'),
]

# Create static products
DEMO_PRODUCTS = [
    DemoProduct(1, 'Wireless Bluetooth Headphones', 2999, 3999, DEMO_CATEGORIES[0], is_featured=True),
    DemoProduct(2, 'Smart Watch Pro', 4999, 6999, DEMO_CATEGORIES[0], is_flash_sale=True),
    DemoProduct(3, 'Cotton T-Shirt', 799, 999, DEMO_CATEGORIES[1], is_featured=True),
    DemoProduct(4, 'Running Shoes', 3499, 4999, DEMO_CATEGORIES[3], is_featured=True),
    DemoProduct(5, 'LED Desk Lamp', 1299, 1699, DEMO_CATEGORIES[2], is_flash_sale=True),
    DemoProduct(6, 'Yoga Mat', 899, 1299, DEMO_CATEGORIES[3]),
    DemoProduct(7, 'Bestseller Novel', 499, 699, DEMO_CATEGORIES[4]),
    DemoProduct(8, 'Portable Speaker', 1999, 2499, DEMO_CATEGORIES[0], is_flash_sale=True),
    DemoProduct(9, 'Denim Jeans', 1499, 1999, DEMO_CATEGORIES[1], is_featured=True),
    DemoProduct(10, 'Garden Tool Set', 2499, 3299, DEMO_CATEGORIES[2]),
    DemoProduct(11, 'Fitness Tracker', 1999, 2999, DEMO_CATEGORIES[0], is_featured=True),
    DemoProduct(12, 'Casual Sneakers', 2499, 3499, DEMO_CATEGORIES[1]),
]

# Create static reviews
DEMO_REVIEWS = [
    DemoReview(1, 5, "Excellent product! Highly recommended.", "Rabin S."),
    DemoReview(2, 4, "Good quality for the price.", "Roshan T."),
    DemoReview(3, 5, "Fast delivery and great packaging.", "Rashmi G."),
    DemoReview(4, 3, "Decent product, meets expectations.", "Aayush K."),
    DemoReview(5, 4, "Would buy again!", "Aone M."),
]

# Create static orders
DEMO_ORDERS = [
    DemoOrder(1, "ORD-001", 5999, "delivered", "2026-01-05", "Rabin Shrestha"),
    DemoOrder(2, "ORD-002", 3499, "processing", "2026-01-06", "Roshan Tamang"),
    DemoOrder(3, "ORD-003", 7999, "pending", "2026-01-07", "Rashmi Gurung"),
    DemoOrder(4, "ORD-004", 2999, "shipped", "2026-01-07", "Aayush Karki"),
    DemoOrder(5, "ORD-005", 4499, "delivered", "2026-01-08", "Aone Maharjan"),
]

# Create static customers
DEMO_CUSTOMERS = [
    DemoCustomer(1, "rabin_shrestha", "rabin@example.com", "2025-11-15"),
    DemoCustomer(2, "roshan_tamang", "roshan@example.com", "2025-12-01"),
    DemoCustomer(3, "rashmi_gurung", "rashmi@example.com", "2025-12-10"),
    DemoCustomer(4, "aayush_karki", "aayush@example.com", "2025-12-20"),
    DemoCustomer(5, "aone_maharjan", "aone@example.com", "2026-01-02"),
]

# Create static messages
DEMO_MESSAGES = [
    DemoMessage(1, "Rabin Shrestha", "rabin@example.com", "Product Inquiry", "I have a question about...", "new", "2026-01-08"),
    DemoMessage(2, "Roshan Tamang", "roshan@example.com", "Order Status", "When will my order arrive?", "read", "2026-01-07"),
    DemoMessage(3, "Rashmi Gurung", "rashmi@example.com", "Return Request", "I would like to return...", "new", "2026-01-06"),
]


# ============== User Demo Views ==============

def user_home(request):
    """Product listing for user demo storefront"""
    products = get_demo_products()
    categories = get_demo_categories()

    return render(request, 'demo/user/home.html', {
        'products': products,
        'categories': categories,
    })


def user_product(request, product_id):
    """Product detail page for user demo"""
    # First try to find in admin-selected products (real products)
    products = get_demo_products()
    product = None
    for p in products:
        if p.id == product_id:
            product = p
            break

    # Fall back to static demo products if not found
    if not product:
        for p in DEMO_PRODUCTS:
            if p.id == product_id:
                product = p
                break

    if not product:
        raise Http404("Demo product not found")

    # Get related products from same category
    related_products = []
    if hasattr(product, 'category') and product.category:
        category_id = product.category.id if hasattr(product.category, 'id') else None
        for p in products:
            if p.id != product_id:
                p_cat_id = p.category.id if hasattr(p, 'category') and p.category and hasattr(p.category, 'id') else None
                if p_cat_id == category_id:
                    related_products.append(p)
                    if len(related_products) >= 4:
                        break

    return render(request, 'demo/user/product.html', {
        'product': product,
        'images': [],
        'related_products': related_products,
    })


def user_cart(request):
    """Cart preview for user demo - STATIC DATA ONLY"""
    return render(request, 'demo/user/cart.html', {
        'cart_items': DEMO_PRODUCTS[:3],
    })


# ============== Admin Demo Views ==============

def admin_dashboard(request):
    """Admin dashboard demo with sample statistics - STATIC DATA ONLY"""
    return render(request, 'demo/admin/dashboard.html', {
        'total_products': len(DEMO_PRODUCTS),
        'total_orders': len(DEMO_ORDERS),
        'total_revenue': 24995,  # Static demo revenue
        'recent_orders': DEMO_ORDERS[:5],
    })


def admin_products(request):
    """Products list for admin demo - STATIC DATA ONLY"""
    return render(request, 'demo/admin/products.html', {
        'products': DEMO_PRODUCTS,
    })


def admin_add_product(request):
    """Add product form demo (non-functional) - STATIC DATA ONLY"""
    return render(request, 'demo/admin/add_product.html', {
        'categories': DEMO_CATEGORIES,
    })


def admin_orders(request):
    """Orders list for admin demo - STATIC DATA ONLY"""
    return render(request, 'demo/admin/orders.html', {
        'orders': DEMO_ORDERS,
    })


# ============== Professional User Demo Views ==============

def pro_user_home(request):
    """Full-featured user storefront demo"""
    # Get admin-selected products or fallback to static data
    products = get_demo_products()
    categories = get_demo_categories()
    flash_sale_products = get_flash_sale_products()
    featured_products = get_featured_products()
    new_arrivals = get_new_arrival_products()

    return render(request, 'demo/pro/user/home.html', {
        'products': products,
        'categories': categories,
        'flash_sale_products': flash_sale_products,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
    })


def pro_user_product(request, product_id):
    """Full-featured product detail demo"""
    # First try to find in admin-selected products (real products)
    products = get_demo_products()
    product = None
    for p in products:
        if p.id == product_id:
            product = p
            break

    # Fall back to static demo products if not found
    if not product:
        for p in DEMO_PRODUCTS:
            if p.id == product_id:
                product = p
                break

    if not product:
        raise Http404("Demo product not found")

    # Get related products from same category
    related_products = []
    if hasattr(product, 'category') and product.category:
        category_id = product.category.id if hasattr(product.category, 'id') else None
        for p in products:
            if p.id != product_id:
                p_cat_id = p.category.id if hasattr(p, 'category') and p.category and hasattr(p.category, 'id') else None
                if p_cat_id == category_id:
                    related_products.append(p)
                    if len(related_products) >= 4:
                        break

    # Calculate average rating from demo reviews
    avg_rating = sum(r.rating for r in DEMO_REVIEWS) / len(DEMO_REVIEWS) if DEMO_REVIEWS else 0

    return render(request, 'demo/pro/user/product.html', {
        'product': product,
        'images': [],
        'reviews': DEMO_REVIEWS,
        'related_products': related_products,
        'avg_rating': avg_rating,
        'review_count': len(DEMO_REVIEWS),
    })


def pro_user_cart(request):
    """Full cart experience demo - STATIC DATA ONLY"""
    cart_items = DEMO_PRODUCTS[:3]
    subtotal = sum(float(p.price) for p in cart_items)
    shipping = 100  # Demo shipping cost
    total = subtotal + shipping

    return render(request, 'demo/pro/user/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
    })


def pro_user_checkout(request):
    """Checkout preview demo - STATIC DATA ONLY"""
    cart_items = DEMO_PRODUCTS[:2]
    subtotal = sum(float(p.price) for p in cart_items)
    shipping = 100
    total = subtotal + shipping

    return render(request, 'demo/pro/user/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
    })


# ============== Professional Admin Demo Views ==============

def pro_admin_dashboard(request):
    """Full admin dashboard with all stats - STATIC DATA ONLY"""
    return render(request, 'demo/pro/admin/dashboard.html', {
        'total_products': len(DEMO_PRODUCTS),
        'total_orders': len(DEMO_ORDERS),
        'total_customers': len(DEMO_CUSTOMERS),
        'total_reviews': len(DEMO_REVIEWS),
        'total_revenue': 24995,
        'pending_orders': 1,
        'processing_orders': 1,
        'completed_orders': 2,
        'recent_orders': DEMO_ORDERS[:5],
        'top_products': DEMO_PRODUCTS[:5],
        'recent_reviews': DEMO_REVIEWS[:5],
    })


def pro_admin_products(request):
    """Full products management demo"""
    products = get_demo_products()
    categories = get_demo_categories()

    # For real products, filter by is_active and stock_quantity
    if products and hasattr(products[0], 'stock_quantity'):
        active_products = [p for p in products if getattr(p, 'is_active', True)]
        out_of_stock = [p for p in products if getattr(p, 'stock_quantity', 100) == 0]
    else:
        active_products = products
        out_of_stock = []

    return render(request, 'demo/pro/admin/products.html', {
        'products': products,
        'categories': categories,
        'total_products': len(products),
        'active_products': len(active_products),
        'out_of_stock': len(out_of_stock),
    })


def pro_admin_orders(request):
    """Full orders management demo - STATIC DATA ONLY"""
    return render(request, 'demo/pro/admin/orders.html', {
        'orders': DEMO_ORDERS,
        'total_orders': len(DEMO_ORDERS),
        'pending': 1,
        'processing': 1,
        'shipped': 1,
        'delivered': 2,
        'cancelled': 0,
    })


def pro_admin_reviews(request):
    """Reviews management demo - STATIC DATA ONLY"""
    avg_rating = sum(r.rating for r in DEMO_REVIEWS) / len(DEMO_REVIEWS) if DEMO_REVIEWS else 0

    return render(request, 'demo/pro/admin/reviews.html', {
        'reviews': DEMO_REVIEWS,
        'total_reviews': len(DEMO_REVIEWS),
        'avg_rating': round(avg_rating, 1),
        'pending_reviews': 0,
    })


def pro_admin_customers(request):
    """Customer management demo - STATIC DATA ONLY"""
    return render(request, 'demo/pro/admin/customers.html', {
        'customers': DEMO_CUSTOMERS,
        'total_customers': len(DEMO_CUSTOMERS),
    })


def pro_admin_analytics(request):
    """Analytics dashboard demo - STATIC DATA ONLY"""
    return render(request, 'demo/pro/admin/analytics.html', {
        'total_revenue': 24995,
        'total_orders': len(DEMO_ORDERS),
        'total_products': len(DEMO_PRODUCTS),
        'total_customers': len(DEMO_CUSTOMERS),
        'top_products': DEMO_PRODUCTS[:10],
        'categories': DEMO_CATEGORIES,
    })


def pro_admin_messages(request):
    """Contact messages demo - STATIC DATA ONLY"""
    unread = [m for m in DEMO_MESSAGES if m.status == 'new']

    return render(request, 'demo/pro/admin/messages.html', {
        'messages': DEMO_MESSAGES,
        'total_messages': len(DEMO_MESSAGES),
        'unread_messages': len(unread),
    })


def pro_admin_storefront(request):
    """Professional demo - Storefront Customization - STATIC DATA ONLY"""
    return render(request, 'demo/pro/admin/storefront.html')
