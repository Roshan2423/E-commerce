"""
Demo API endpoints - Returns admin-selected products for demo pages
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from products.models import Review

# Import helper functions from views
from .views import (
    get_demo_products,
    get_demo_categories,
    get_featured_products,
    get_flash_sale_products,
    get_new_arrival_products,
    DEMO_PRODUCTS,
    DEMO_CATEGORIES,
    DEMO_REVIEWS,
)


def serialize_product(product):
    """Serialize a product (real or demo) to JSON-friendly dict"""
    # Check if it's a real Product model or demo object
    if hasattr(product, 'get_main_image'):
        main_image = product.get_main_image()
    else:
        main_image = None

    # Use placeholder for missing images (fast loading)
    if not main_image:
        # Use picsum for random product images (lightweight)
        product_id = getattr(product, 'id', 1)
        main_image = f'https://picsum.photos/seed/{product_id}/400/400'

    # Handle price (could be Decimal or int)
    try:
        price = float(str(product.price))
    except (ValueError, TypeError):
        price = 0.0

    # Handle compare_price
    try:
        compare_price = float(str(product.compare_price)) if product.compare_price else None
    except (ValueError, TypeError, AttributeError):
        compare_price = None

    # Get category name
    if hasattr(product, 'category') and product.category:
        if hasattr(product.category, 'name'):
            category_name = product.category.name
        else:
            category_name = str(product.category)
    else:
        category_name = 'Uncategorized'

    # Get rating/reviews for real products
    avg_rating = 0
    review_count = 0
    if hasattr(product, 'pk') and product.pk:
        try:
            product_reviews = Review.objects.filter(product=product, status='approved')
            review_count = product_reviews.count()
            if review_count > 0:
                total_rating = sum([r.rating for r in product_reviews])
                avg_rating = round(total_rating / review_count, 1)
        except Exception:
            pass

    return {
        'id': getattr(product, 'id', 0),
        'name': getattr(product, 'name', ''),
        'description': getattr(product, 'description', ''),
        'price': price,
        'compare_price': compare_price,
        'category': category_name,
        'stock': getattr(product, 'stock_quantity', 100),
        'stock_status': getattr(product, 'stock_status', 'in_stock'),
        'image': main_image,
        'sku': getattr(product, 'sku', ''),
        'rating': avg_rating,
        'reviews': review_count,
        'is_featured': getattr(product, 'is_featured', False),
        'is_flash_sale': getattr(product, 'is_flash_sale', False),
    }


def serialize_category(category):
    """Serialize a category (real or demo) to JSON-friendly dict"""
    return {
        'id': getattr(category, 'id', 0),
        'name': getattr(category, 'name', ''),
        'slug': getattr(category, 'slug', ''),
        'description': getattr(category, 'description', ''),
    }


@require_GET
def demo_products_api(request):
    """Get demo products (admin-selected or fallback)"""
    try:
        products = get_demo_products()
        products_data = [serialize_product(p) for p in products]

        return JsonResponse({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def demo_flash_sale_api(request):
    """Get demo flash sale products"""
    try:
        products = get_flash_sale_products()
        products_data = [serialize_product(p) for p in products]

        return JsonResponse({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def demo_featured_api(request):
    """Get demo featured products"""
    try:
        products = get_featured_products()
        products_data = [serialize_product(p) for p in products]

        return JsonResponse({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def demo_new_arrivals_api(request):
    """Get demo new arrival products"""
    try:
        products = get_new_arrival_products()
        products_data = [serialize_product(p) for p in products]

        return JsonResponse({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def demo_categories_api(request):
    """Get demo categories"""
    try:
        categories = get_demo_categories()
        categories_data = [serialize_category(c) for c in categories]

        return JsonResponse({
            'success': True,
            'categories': categories_data,
            'count': len(categories_data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def demo_product_detail_api(request, product_id):
    """Get single demo product details"""
    try:
        products = get_demo_products()

        # Find product by ID
        product = None
        for p in products:
            if getattr(p, 'id', 0) == product_id:
                product = p
                break

        if not product:
            # Try in static demo products
            for p in DEMO_PRODUCTS:
                if p.id == product_id:
                    product = p
                    break

        if not product:
            return JsonResponse({
                'success': False,
                'error': 'Product not found'
            }, status=404)

        return JsonResponse({
            'success': True,
            'product': serialize_product(product)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def demo_site_stats_api(request):
    """Get demo site statistics"""
    try:
        products = get_demo_products()

        return JsonResponse({
            'success': True,
            'stats': {
                'total_customers': 1250,  # Demo stat
                'avg_rating': 4.8,  # Demo stat
                'total_products': len(products),
                'total_reviews': 500,  # Demo stat
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
