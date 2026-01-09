"""
API views for products - Frontend integration
"""
import json
import base64
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from .models import Product, Category, Review, ReviewImage
from orders.models import Order


@require_GET
def products_api(request):
    """Get all active products for store frontend (admin products only, not vendor products)"""
    try:
        # Only show products added by admin (no vendor), vendor products are shown in their storefronts
        products = Product.objects.filter(is_active=True, vendor__isnull=True).select_related('category')

        # Apply filters
        category = request.GET.get('category')
        if category:
            products = products.filter(category__slug=category)

        search = request.GET.get('search')
        if search:
            products = products.filter(name__icontains=search)

        products_data = []
        for product in products[:50]:  # Limit to 50 products
            # Get main image
            main_image = product.images.filter(is_main=True).first()
            if not main_image:
                main_image = product.images.first()

            image_url = main_image.image.url if main_image else None

            # Get review stats
            reviews = Review.objects.filter(product=product, status='approved')
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
            review_count = reviews.count()

            products_data.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'category': product.category.name if product.category else 'Uncategorized',
                'category_slug': product.category.slug if product.category else '',
                'price': float(product.price),
                'compare_price': float(product.compare_price) if product.compare_price else None,
                'image': image_url,
                'rating': round(avg_rating, 1),
                'reviews': review_count,
                'stock_status': 'in_stock' if product.stock_quantity > 10 else ('low_stock' if product.stock_quantity > 0 else 'out_of_stock'),
                'description': product.description,
                'short_description': product.short_description or product.description[:100] if product.description else '',
            })

        return JsonResponse({
            'success': True,
            'products': products_data,
            'total': len(products_data)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
def flash_sale_api(request):
    """Get flash sale products for store frontend (admin products only)"""
    try:
        # Only show admin products (no vendor), vendor products are shown in their storefronts
        products = Product.objects.filter(
            is_active=True,
            is_flash_sale=True,
            vendor__isnull=True
        ).select_related('category')

        products_data = []
        for product in products[:12]:
            main_image = product.images.filter(is_main=True).first()
            if not main_image:
                main_image = product.images.first()

            image_url = main_image.image.url if main_image else None

            reviews = Review.objects.filter(product=product, status='approved')
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
            review_count = reviews.count()

            # Calculate discount percentage
            original_price = float(product.compare_price or product.price)
            sale_price = float(product.flash_sale_price or product.price)
            discount = int(((original_price - sale_price) / original_price) * 100) if original_price > sale_price else 0

            products_data.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'category': product.category.name if product.category else 'Uncategorized',
                'price': sale_price,
                'compare_price': original_price,
                'discount': discount,
                'image': image_url,
                'rating': round(avg_rating, 1),
                'reviews': review_count,
                'stock_status': 'in_stock' if product.stock_quantity > 10 else ('low_stock' if product.stock_quantity > 0 else 'out_of_stock'),
            })

        return JsonResponse({
            'success': True,
            'products': products_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
def categories_api(request):
    """Get all active categories for store frontend"""
    try:
        categories = Category.objects.filter(is_active=True)

        categories_data = []
        for category in categories:
            product_count = Product.objects.filter(category=category, is_active=True).count()

            categories_data.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'icon': category.icon or 'fa-shopping-basket',
                'description': category.description or '',
                'image': category.image.url if category.image else None,
                'product_count': product_count,
            })

        return JsonResponse({
            'success': True,
            'categories': categories_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
def product_detail_api(request, product_id):
    """Get product details for store frontend (admin products only)"""
    try:
        # Only show admin products (no vendor), vendor products are shown in their storefronts
        product = Product.objects.select_related('category').get(id=product_id, is_active=True, vendor__isnull=True)

        # Get all images
        images = []
        for img in product.images.all():
            images.append({
                'url': img.image.url,
                'alt': img.alt_text or product.name,
                'is_main': img.is_main
            })

        # Get review stats
        reviews = Review.objects.filter(product=product, status='approved')
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = reviews.count()

        # Main image
        main_image = product.images.filter(is_main=True).first()
        if not main_image:
            main_image = product.images.first()

        product_data = {
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'category': product.category.name if product.category else 'Uncategorized',
            'category_slug': product.category.slug if product.category else '',
            'price': float(product.price),
            'compare_price': float(product.compare_price) if product.compare_price else None,
            'image': main_image.image.url if main_image else None,
            'images': images,
            'rating': round(avg_rating, 1),
            'reviews': review_count,
            'stock_quantity': product.stock_quantity,
            'stock_status': 'in_stock' if product.stock_quantity > 10 else ('low_stock' if product.stock_quantity > 0 else 'out_of_stock'),
            'description': product.description,
            'short_description': product.short_description or '',
            'is_flash_sale': product.is_flash_sale,
            'flash_sale_price': float(product.flash_sale_price) if product.flash_sale_price else None,
        }

        return JsonResponse({
            'success': True,
            'product': product_data
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
def product_reviews_api(request, product_id):
    """Get approved reviews for a product"""
    try:
        product = Product.objects.get(id=product_id)
        reviews = Review.objects.filter(product=product, status='approved').order_by('-created_at')

        reviews_data = []
        for review in reviews:
            # Get review images
            images = [{'url': img.image.url, 'alt': img.alt_text} for img in review.images.all()]

            reviews_data.append({
                'id': review.id,
                'user': review.user.first_name or review.user.username,
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment,
                'images': images,
                'is_verified_purchase': review.is_verified_purchase,
                'helpful_count': review.helpful_count,
                'admin_response': review.admin_response,
                'created_at': review.created_at.strftime('%B %d, %Y'),
            })

        # Calculate average rating
        total_reviews = len(reviews_data)
        avg_rating = sum(r['rating'] for r in reviews_data) / total_reviews if total_reviews > 0 else 0

        # Rating distribution
        rating_dist = {i: 0 for i in range(1, 6)}
        for r in reviews_data:
            rating_dist[r['rating']] += 1

        return JsonResponse({
            'success': True,
            'reviews': reviews_data,
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 1),
            'rating_distribution': rating_dist,
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
def can_review_product(request, product_id):
    """Check if current user can review a product (must have delivered order)"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': True,
            'can_review': False,
            'reason': 'login_required',
            'message': 'Please login to write a review'
        })

    try:
        product = Product.objects.get(id=product_id)

        # Check if user has already reviewed this product
        existing_review = Review.objects.filter(product=product, user=request.user).exists()
        if existing_review:
            return JsonResponse({
                'success': True,
                'can_review': False,
                'reason': 'already_reviewed',
                'message': 'You have already reviewed this product'
            })

        # Check if user has a delivered order containing this product
        delivered_orders = Order.objects.filter(
            user=request.user,
            status='delivered'
        )

        has_purchased = False
        eligible_order = None
        for order in delivered_orders:
            # Check if this order contains the product
            order_items = order.items.filter(product=product)
            if order_items.exists():
                # Check if user already reviewed for this order
                if not Review.objects.filter(product=product, user=request.user, order=order).exists():
                    has_purchased = True
                    eligible_order = str(order.order_id)
                    break

        if has_purchased:
            return JsonResponse({
                'success': True,
                'can_review': True,
                'order_id': eligible_order,
                'message': 'You can write a review for this product'
            })
        else:
            return JsonResponse({
                'success': True,
                'can_review': False,
                'reason': 'no_purchase',
                'message': 'You can only review products from delivered orders'
            })

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def submit_review(request, product_id):
    """Submit a review for a product"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Please login to submit a review'
        }, status=401)

    try:
        data = json.loads(request.body)
        product = Product.objects.get(id=product_id)

        # Verify user can review
        order_id = data.get('order_id')
        order = None
        if order_id:
            order = Order.objects.get(order_id=order_id, user=request.user, status='delivered')
            # Verify product is in this order
            if not order.items.filter(product=product).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'This product is not in the specified order'
                }, status=400)
        else:
            # Find any delivered order with this product
            for o in Order.objects.filter(user=request.user, status='delivered'):
                if o.items.filter(product=product).exists():
                    if not Review.objects.filter(product=product, user=request.user, order=o).exists():
                        order = o
                        break

        if not order:
            return JsonResponse({
                'success': False,
                'error': 'You must purchase and receive this product before reviewing'
            }, status=403)

        # Check for existing review
        if Review.objects.filter(product=product, user=request.user, order=order).exists():
            return JsonResponse({
                'success': False,
                'error': 'You have already reviewed this product for this order'
            }, status=400)

        # Create the review
        review = Review.objects.create(
            product=product,
            user=request.user,
            order=order,
            rating=int(data.get('rating', 5)),
            title=data.get('title', ''),
            comment=data.get('comment', ''),
            is_verified_purchase=True,
            status='approved'  # Auto-approve reviews
        )

        # Process images
        images = data.get('images', [])
        for idx, img_data in enumerate(images[:5]):  # Max 5 images
            if img_data.startswith('data:image'):
                try:
                    format_part, imgstr = img_data.split(';base64,')
                    ext = format_part.split('/')[-1]
                    img_bytes = base64.b64decode(imgstr)
                    file_name = f"review_{review.id}_{idx}.{ext}"
                    img_file = ContentFile(img_bytes, name=file_name)
                    ReviewImage.objects.create(
                        review=review,
                        image=img_file,
                        alt_text=f"Review image {idx + 1}"
                    )
                except Exception as e:
                    print(f"Error saving review image: {e}")
                    continue

        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your review has been submitted and is pending approval.',
            'review_id': review.id
        })

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
@login_required
def my_reviews_api(request):
    """Get all reviews by the current user"""
    try:
        reviews = Review.objects.filter(user=request.user).select_related('product', 'order').order_by('-created_at')

        reviews_data = []
        for review in reviews:
            # Get review images
            images = [{'url': img.image.url, 'alt': img.alt_text} for img in review.images.all()]

            # Get product image
            product_image = review.product.get_main_image() if review.product else None

            reviews_data.append({
                'id': review.id,
                'product': {
                    'id': review.product.id,
                    'name': review.product.name,
                    'image': product_image,
                    'slug': review.product.slug if hasattr(review.product, 'slug') else '',
                },
                'order_id': str(review.order.order_id)[:8].upper() if review.order else None,
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment,
                'images': images,
                'status': review.status,
                'status_display': review.get_status_display(),
                'admin_response': review.admin_response,
                'is_verified_purchase': review.is_verified_purchase,
                'helpful_count': review.helpful_count,
                'created_at': review.created_at.strftime('%B %d, %Y'),
                'updated_at': review.updated_at.strftime('%B %d, %Y'),
            })

        # Stats
        total_reviews = len(reviews_data)
        approved_count = sum(1 for r in reviews_data if r['status'] == 'approved')
        pending_count = sum(1 for r in reviews_data if r['status'] == 'pending')
        avg_rating = sum(r['rating'] for r in reviews_data) / total_reviews if total_reviews > 0 else 0

        return JsonResponse({
            'success': True,
            'reviews': reviews_data,
            'stats': {
                'total': total_reviews,
                'approved': approved_count,
                'pending': pending_count,
                'average_rating': round(avg_rating, 1),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
def site_stats_api(request):
    """Get site statistics for store frontend (admin products only)"""
    try:
        # Only count admin products (no vendor)
        stats = {
            'total_products': Product.objects.filter(is_active=True, vendor__isnull=True).count(),
            'total_categories': Category.objects.filter(is_active=True).count(),
            'total_reviews': Review.objects.filter(status='approved', product__vendor__isnull=True).count(),
        }

        return JsonResponse({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
