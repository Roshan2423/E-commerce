"""
Public Storefront API Views
These APIs are used by the public storefront pages
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.views.decorators.http import require_GET
from .models import Business, VendorStorefront


def get_vendor_from_slug(slug):
    """Helper to get vendor from URL slug"""
    return get_object_or_404(Business, slug=slug, status='approved')


# ============================================
# Storefront Page Views (Server-rendered)
# ============================================

def storefront_home(request, vendor_slug, spa_path=None):
    """Public storefront home page - Server-rendered version"""
    from products.models import Category
    from products.models import Review

    vendor = get_vendor_from_slug(vendor_slug)
    storefront = getattr(vendor, 'storefront', None)

    # Get counts for stats
    product_count = vendor.products.filter(is_active=True).count()
    category_count = vendor.products.filter(is_active=True).values('category').distinct().count()

    # Get recent products
    recent_products = vendor.products.filter(is_active=True).order_by('-created_at')[:12]

    # Get featured products - sorted by view_count (most clicked first)
    # If no featured products exist, show most viewed products instead
    featured_products = vendor.products.filter(is_active=True, is_featured=True).order_by('-view_count')[:8]
    if not featured_products.exists():
        # Fallback: show most viewed products as featured
        featured_products = vendor.products.filter(is_active=True).order_by('-view_count')[:8]

    # Get categories with products from this vendor (with product counts)
    category_ids = vendor.products.filter(is_active=True).values_list('category_id', flat=True).distinct()
    categories = Category.objects.filter(id__in=category_ids).annotate(
        product_count=Count('products', filter=Q(products__vendor=vendor, products__is_active=True))
    )

    # Get flash sale products (available for all plans)
    flash_sale_products = vendor.products.filter(is_active=True, is_flash_sale=True)[:6]

    context = {
        'vendor': vendor,
        'storefront': storefront,
        'product_count': product_count,
        'category_count': category_count,
        'recent_products': recent_products,
        'featured_products': featured_products,
        'categories': categories,
        'flash_sale_products': flash_sale_products,
    }

    # Professional plan uses professional template, starter uses simple template
    if vendor.plan == 'professional':
        return render(request, 'storefront/professional/home.html', context)
    return render(request, 'storefront/home.html', context)


def storefront_products_page(request, vendor_slug):
    """Public storefront products listing page"""
    vendor = get_vendor_from_slug(vendor_slug)
    storefront = getattr(vendor, 'storefront', None)

    products = vendor.products.filter(is_active=True)

    # Filter by category
    category = request.GET.get('category')
    if category:
        products = products.filter(category__slug=category)

    # Search
    search = request.GET.get('q')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-created_at')

    # Pagination
    per_page = storefront.products_per_page if storefront else 12
    paginator = Paginator(products, per_page)
    page = request.GET.get('page', 1)
    products = paginator.get_page(page)

    # Get categories for filter
    categories = vendor.products.filter(
        is_active=True
    ).values(
        'category__id',
        'category__name',
        'category__slug'
    ).annotate(
        count=Count('id')
    ).distinct()

    context = {
        'vendor': vendor,
        'storefront': storefront,
        'products': products,
        'categories': categories,
        'current_category': category,
        'search_query': search,
        'current_sort': sort,
    }
    return render(request, 'storefront/products.html', context)


def storefront_product_detail_page(request, vendor_slug, product_id):
    """Public storefront product detail page"""
    from django.db.models import F

    vendor = get_vendor_from_slug(vendor_slug)
    storefront = getattr(vendor, 'storefront', None)

    product = get_object_or_404(
        vendor.products,
        id=product_id,
        is_active=True
    )

    # Increment view count (atomic operation to prevent race conditions)
    vendor.products.filter(id=product_id).update(view_count=F('view_count') + 1)

    # Get related products
    related_products = vendor.products.filter(
        is_active=True,
        category=product.category
    ).exclude(id=product.id)[:4]

    # Get reviews
    reviews = product.reviews.filter(status='approved').order_by('-created_at')[:10]
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    context = {
        'vendor': vendor,
        'storefront': storefront,
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': reviews.count(),
    }
    return render(request, 'storefront/product_detail.html', context)


# ============================================
# Storefront API Endpoints
# ============================================

@require_GET
def storefront_config_api(request, vendor_slug):
    """Get storefront configuration (colors, hero, etc.)"""
    vendor = get_vendor_from_slug(vendor_slug)
    storefront = getattr(vendor, 'storefront', None)

    config = {
        'business': {
            'id': vendor.id,
            'name': vendor.business_name,
            'slug': vendor.slug,
            'description': vendor.description,
            'logo': storefront.logo.url if storefront and storefront.logo else None,
        },
        'hero': {
            'image': storefront.hero_image.url if storefront and storefront.hero_image else None,
            'title': storefront.hero_title if storefront else vendor.business_name,
            'subtitle': storefront.hero_subtitle if storefront else vendor.description,
            'cta_text': storefront.hero_cta_text if storefront else 'Shop Now',
            'cta_link': storefront.hero_cta_link if storefront else '/products',
        },
        'theme': {
            'primary_color': storefront.primary_color if storefront else '#6366f1',
            'secondary_color': storefront.secondary_color if storefront else '#8b5cf6',
            'accent_color': storefront.accent_color if storefront else '#ec4899',
        },
        'layout': {
            'product_layout': storefront.product_layout if storefront else 'grid',
            'products_per_page': storefront.products_per_page if storefront else 12,
            'show_flash_sale': storefront.show_flash_sale if storefront else True,
            'show_featured': storefront.show_featured if storefront else True,
            'show_categories': storefront.show_categories if storefront else True,
            'show_new_arrivals': storefront.show_new_arrivals if storefront else True,
            'show_testimonials': storefront.show_testimonials if storefront else True,
            'show_newsletter': storefront.show_newsletter if storefront else True,
            'show_hero': storefront.show_hero if storefront else True,
        },
        'social': {
            'facebook': storefront.facebook_url if storefront else None,
            'instagram': storefront.instagram_url if storefront else None,
            'twitter': storefront.twitter_url if storefront else None,
            'tiktok': storefront.tiktok_url if storefront else None,
            'youtube': storefront.youtube_url if storefront else None,
        },
        'seo': {
            'meta_title': storefront.meta_title if storefront else vendor.business_name,
            'meta_description': storefront.meta_description if storefront else vendor.description,
        }
    }

    return JsonResponse(config)


@require_GET
def storefront_products_api(request, vendor_slug):
    """Get vendor's products as JSON"""
    from django.utils import timezone
    from datetime import timedelta

    vendor = get_vendor_from_slug(vendor_slug)
    storefront = getattr(vendor, 'storefront', None)

    products = vendor.products.filter(is_active=True)

    # Filter by category
    category = request.GET.get('category')
    if category:
        products = products.filter(category__slug=category)

    # Filter by type (featured, new_arrivals, popular)
    product_type = request.GET.get('type')
    if product_type == 'featured':
        # Featured products sorted by view count (most clicked first)
        featured_products = products.filter(is_featured=True).order_by('-view_count')
        if not featured_products.exists():
            # Fallback: most viewed products
            products = products.order_by('-view_count')
        else:
            products = featured_products
    elif product_type == 'new_arrivals':
        # New arrivals from last 30 days
        month_ago = timezone.now() - timedelta(days=30)
        new_products = products.filter(created_at__gte=month_ago).order_by('-created_at')
        if not new_products.exists():
            # Fallback: newest products
            products = products.order_by('-created_at')
        else:
            products = new_products
    elif product_type == 'popular':
        # Most viewed products
        products = products.order_by('-view_count')

    # Filter by featured (legacy param)
    featured = request.GET.get('featured')
    if featured == 'true':
        products = products.filter(is_featured=True)

    # Search
    search = request.GET.get('q')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    # Sorting (only if not using type filter which has its own sorting)
    sort = request.GET.get('sort', '-created_at')
    if not product_type:  # Only apply sort if no type filter
        if sort == 'price_low':
            products = products.order_by('price')
        elif sort == 'price_high':
            products = products.order_by('-price')
        elif sort == 'name':
            products = products.order_by('name')
        elif sort == 'popular':
            products = products.order_by('-view_count')
        else:
            products = products.order_by('-created_at')

    # Pagination
    per_page = int(request.GET.get('per_page', storefront.products_per_page if storefront else 12))
    page = int(request.GET.get('page', 1))
    paginator = Paginator(products, per_page)
    page_obj = paginator.get_page(page)

    # Build response
    products_data = []
    for product in page_obj:
        # Get review stats for this product
        approved_reviews = product.reviews.filter(status='approved')
        avg_rating = approved_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = approved_reviews.count()

        products_data.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'compare_price': float(product.compare_price) if product.compare_price else None,
            'discount_percentage': product.get_discount_percentage(),
            'image': product.get_main_image(),
            'category': {
                'id': product.category.id,
                'name': product.category.name,
                'slug': product.category.slug,
            } if product.category else None,
            'stock_status': product.stock_status,
            'is_featured': product.is_featured,
            'is_flash_sale': product.is_flash_sale,
            'flash_sale_price': float(product.flash_sale_price) if product.flash_sale_price else None,
            'rating': round(avg_rating, 1),
            'reviews': review_count,
        })

    return JsonResponse({
        'success': True,
        'products': products_data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_products': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


@require_GET
def storefront_product_detail_api(request, vendor_slug, product_id):
    """Get single product details as JSON"""
    from django.db.models import F

    vendor = get_vendor_from_slug(vendor_slug)

    product = get_object_or_404(
        vendor.products,
        id=product_id,
        is_active=True
    )

    # Increment view count (atomic operation to prevent race conditions)
    vendor.products.filter(id=product_id).update(view_count=F('view_count') + 1)

    # Get all images
    images = []
    for img in product.images.all():
        images.append({
            'id': img.id,
            'url': img.image.url if img.image else None,
            'alt': img.alt_text,
            'is_main': img.is_main,
        })

    # Get variants
    variants = []
    for variant in product.variants.filter(is_active=True):
        variants.append({
            'id': variant.id,
            'name': variant.name,
            'value': variant.value,
            'price_adjustment': str(variant.price_adjustment),
            'stock_quantity': variant.stock_quantity,
            'sku': variant.sku,
        })

    # Get reviews summary
    reviews = product.reviews.filter(status='approved')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    product_data = {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'description': product.description,
        'short_description': product.short_description,
        'price': float(product.price),
        'compare_price': float(product.compare_price) if product.compare_price else None,
        'discount_percentage': product.get_discount_percentage(),
        'sku': product.sku,
        'stock_quantity': product.stock_quantity,
        'stock_status': product.stock_status,
        'is_featured': product.is_featured,
        'is_flash_sale': product.is_flash_sale,
        'flash_sale_price': float(product.flash_sale_price) if product.flash_sale_price else None,
        'category': {
            'id': product.category.id,
            'name': product.category.name,
            'slug': product.category.slug,
        } if product.category else None,
        'images': images,
        'variants': variants,
        'reviews': {
            'average_rating': round(avg_rating, 1),
            'total_count': reviews.count(),
        }
    }

    return JsonResponse(product_data)


@require_GET
def storefront_flash_sale_api(request, vendor_slug):
    """Get vendor's flash sale products"""
    vendor = get_vendor_from_slug(vendor_slug)
    storefront = getattr(vendor, 'storefront', None)

    # Check if flash sale section is enabled
    if storefront and not storefront.show_flash_sale:
        return JsonResponse({
            'success': True,
            'products': [],
            'count': 0,
            'enabled': False,
        })

    products = vendor.products.filter(
        is_active=True,
        is_flash_sale=True
    )[:8]

    products_data = []
    for product in products:
        # Get review stats
        approved_reviews = product.reviews.filter(status='approved')
        avg_rating = approved_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = approved_reviews.count()

        products_data.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'flash_sale_price': float(product.flash_sale_price) if product.flash_sale_price else float(product.price),
            'compare_price': float(product.compare_price) if product.compare_price else None,
            'discount_percentage': product.get_discount_percentage(),
            'image': product.get_main_image(),
            'stock_status': product.stock_status,
            'rating': round(avg_rating, 1),
            'reviews': review_count,
        })

    return JsonResponse({
        'success': True,
        'products': products_data,
        'count': len(products_data),
        'enabled': True,
    })


@require_GET
def storefront_categories_api(request, vendor_slug):
    """Get all active categories for this vendor's storefront"""
    from products.models import Category

    vendor = get_vendor_from_slug(vendor_slug)
    storefront = getattr(vendor, 'storefront', None)

    # Check if categories section is enabled
    if storefront and not storefront.show_categories:
        return JsonResponse({
            'success': True,
            'categories': [],
            'count': 0,
            'enabled': False,
        })

    # Get ALL active categories and count vendor's products in each
    categories = Category.objects.filter(is_active=True).order_by('name')

    categories_data = []
    for category in categories:
        # Count products from this vendor in this category
        product_count = vendor.products.filter(
            is_active=True,
            category=category
        ).count()

        categories_data.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'icon': category.icon or 'fa-shopping-basket',
            'image': category.image.url if category.image else None,
            'product_count': product_count,
        })

    return JsonResponse({
        'success': True,
        'categories': categories_data,
        'count': len(categories_data),
        'enabled': True,
    })


@require_GET
def storefront_featured_api(request, vendor_slug):
    """Get vendor's featured products - sorted by view count (most clicked first)"""
    vendor = get_vendor_from_slug(vendor_slug)
    storefront = getattr(vendor, 'storefront', None)

    # Check if featured section is enabled
    if storefront and not storefront.show_featured:
        return JsonResponse({
            'success': True,
            'products': [],
            'count': 0,
            'enabled': False,
        })

    # Get featured products sorted by view count
    products = vendor.products.filter(is_active=True, is_featured=True).order_by('-view_count')[:8]

    # Fallback to most viewed products if no featured products
    if not products.exists():
        products = vendor.products.filter(is_active=True).order_by('-view_count')[:8]

    products_data = []
    for product in products:
        # Get review stats
        approved_reviews = product.reviews.filter(status='approved')
        avg_rating = approved_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = approved_reviews.count()

        products_data.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'compare_price': float(product.compare_price) if product.compare_price else None,
            'discount_percentage': product.get_discount_percentage(),
            'image': product.get_main_image(),
            'stock_status': product.stock_status,
            'is_featured': product.is_featured,
            'view_count': product.view_count,
            'rating': round(avg_rating, 1),
            'reviews': review_count,
        })

    return JsonResponse({
        'success': True,
        'products': products_data,
        'count': len(products_data),
        'enabled': True,
    })


@require_GET
def storefront_new_arrivals_api(request, vendor_slug):
    """Get vendor's new arrival products - sorted by creation date"""
    from django.utils import timezone
    from datetime import timedelta

    vendor = get_vendor_from_slug(vendor_slug)
    storefront = getattr(vendor, 'storefront', None)

    # Check if new arrivals section is enabled
    if storefront and not storefront.show_new_arrivals:
        return JsonResponse({
            'success': True,
            'products': [],
            'count': 0,
            'enabled': False,
        })

    # Get products from last 30 days
    month_ago = timezone.now() - timedelta(days=30)
    products = vendor.products.filter(
        is_active=True,
        created_at__gte=month_ago
    ).order_by('-created_at')[:8]

    # Fallback to newest products if no recent products
    if not products.exists():
        products = vendor.products.filter(is_active=True).order_by('-created_at')[:8]

    products_data = []
    for product in products:
        # Get review stats
        approved_reviews = product.reviews.filter(status='approved')
        avg_rating = approved_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = approved_reviews.count()

        products_data.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'compare_price': float(product.compare_price) if product.compare_price else None,
            'discount_percentage': product.get_discount_percentage(),
            'image': product.get_main_image(),
            'stock_status': product.stock_status,
            'created_at': product.created_at.isoformat(),
            'rating': round(avg_rating, 1),
            'reviews': review_count,
        })

    return JsonResponse({
        'success': True,
        'products': products_data,
        'count': len(products_data),
        'enabled': True,
    })


@require_GET
def storefront_product_reviews_api(request, vendor_slug, product_id):
    """Get reviews for a specific product"""
    vendor = get_vendor_from_slug(vendor_slug)

    product = get_object_or_404(
        vendor.products,
        id=product_id,
        is_active=True
    )

    # Get approved reviews
    reviews = product.reviews.filter(status='approved').order_by('-created_at')

    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))
    paginator = Paginator(reviews, per_page)
    page_obj = paginator.get_page(page)

    reviews_data = []
    for review in page_obj:
        # Format date nicely
        created_date = review.created_at.strftime('%B %d, %Y') if review.created_at else ''

        # Get review images if any
        review_images = []
        if hasattr(review, 'images'):
            for img in review.images.all():
                review_images.append({
                    'url': img.image.url if img.image else '',
                    'alt': getattr(img, 'alt_text', 'Review image')
                })

        reviews_data.append({
            'id': review.id,
            'rating': review.rating,
            'title': getattr(review, 'title', '') or '',
            'comment': review.comment,
            'user': review.user.get_full_name() or review.user.username if review.user else 'Anonymous',
            'created_at': created_date,
            'is_verified_purchase': getattr(review, 'verified_purchase', False),
            'images': review_images,
            'admin_response': getattr(review, 'vendor_response', '') or '',
            'helpful_count': getattr(review, 'helpful_count', 0) or 0,
        })

    # Calculate rating distribution
    rating_distribution = {}
    all_reviews = product.reviews.filter(status='approved')
    total = all_reviews.count()
    for i in range(1, 6):
        count = all_reviews.filter(rating=i).count()
        rating_distribution[i] = {
            'count': count,
            'percentage': round((count / total * 100) if total > 0 else 0, 1)
        }

    avg_rating = all_reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    # Response format that app.js expects
    return JsonResponse({
        'success': True,
        'reviews': reviews_data,
        'total_reviews': total,
        'average_rating': round(avg_rating, 1),
        'rating_distribution': {str(k): v['count'] for k, v in rating_distribution.items()},
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


@require_GET
def storefront_related_products_api(request, vendor_slug, product_id):
    """Get related products (You May Also Like) for a product"""
    vendor = get_vendor_from_slug(vendor_slug)

    product = get_object_or_404(
        vendor.products,
        id=product_id,
        is_active=True
    )

    # Get related products from same category, excluding current product
    related_products = vendor.products.filter(
        is_active=True,
        category=product.category
    ).exclude(id=product.id).order_by('-view_count')[:8]

    # If not enough related products, fill with popular products from vendor
    if related_products.count() < 4:
        exclude_ids = [product.id] + list(related_products.values_list('id', flat=True))
        additional = vendor.products.filter(
            is_active=True
        ).exclude(
            id__in=exclude_ids
        ).order_by('-view_count')[:8 - related_products.count()]
        related_products = list(related_products) + list(additional)

    products_data = []
    for prod in related_products:
        # Get review stats
        approved_reviews = prod.reviews.filter(status='approved')
        avg_rating = approved_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = approved_reviews.count()

        products_data.append({
            'id': prod.id,
            'name': prod.name,
            'slug': prod.slug,
            'price': float(prod.price),
            'compare_price': float(prod.compare_price) if prod.compare_price else None,
            'discount_percentage': prod.get_discount_percentage(),
            'image': prod.get_main_image(),
            'stock_status': prod.stock_status,
            'category': {
                'id': prod.category.id,
                'name': prod.category.name,
                'slug': prod.category.slug,
            } if prod.category else None,
            'rating': round(avg_rating, 1),
            'reviews': review_count,
        })

    return JsonResponse({
        'success': True,
        'products': products_data,
        'count': len(products_data),
    })


@require_GET
def storefront_can_review_api(request, vendor_slug, product_id):
    """Check if current user can review a product"""
    from orders.models import Order, OrderItem

    vendor = get_vendor_from_slug(vendor_slug)

    product = get_object_or_404(
        vendor.products,
        id=product_id,
        is_active=True
    )

    # Check if user is logged in
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': True,
            'can_review': False,
            'reason': 'login_required',
            'message': 'Please log in to write a review'
        })

    # Check if user already reviewed this product
    existing_review = product.reviews.filter(user=request.user).exists()
    if existing_review:
        return JsonResponse({
            'success': True,
            'can_review': False,
            'reason': 'already_reviewed',
            'message': 'You have already reviewed this product'
        })

    # Check if user has purchased this product (from this vendor)
    order_item = OrderItem.objects.filter(
        order__user=request.user,
        order__status='delivered',
        product=product
    ).first()

    if not order_item:
        return JsonResponse({
            'success': True,
            'can_review': False,
            'reason': 'no_purchase',
            'message': 'You can only review products you have purchased'
        })

    return JsonResponse({
        'success': True,
        'can_review': True,
        'order_id': str(order_item.order.order_id),
        'message': 'You can review this product'
    })
