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
from .models import Product, Category, Review, ReviewImage
from orders.models import Order


@require_GET
def products_api(request):
    """Get all active products for frontend"""
    try:
        # Workaround for Djongo bug with boolean filters
        # Get all products and filter in Python instead
        all_products = Product.objects.all().order_by('-created_at')
        products = [p for p in all_products if p.is_active]
        
        products_data = []
        for product in products:
            # Get the main image from ProductImage model
            main_image = product.get_main_image()
            if not main_image:
                main_image = '/static/images/placeholder.jpg'
            
            # Handle Decimal128 from MongoDB
            try:
                price = float(str(product.price))
            except (ValueError, TypeError):
                price = 0.0

            # Get compare_price (special price)
            try:
                compare_price = float(str(product.compare_price)) if product.compare_price else None
            except (ValueError, TypeError):
                compare_price = None

            # Get actual rating and review count
            product_reviews = Review.objects.filter(product=product, status='approved')
            review_count = product_reviews.count()
            avg_rating = 0
            if review_count > 0:
                total_rating = sum([r.rating for r in product_reviews])
                avg_rating = round(total_rating / review_count, 1)

            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': price,
                'compare_price': compare_price,
                'category': product.category.name if product.category else 'Uncategorized',
                'category_id': product.category.id if product.category else None,
                'stock': product.stock_quantity,
                'stock_status': product.stock_status,
                'image': main_image,
                'sku': product.sku,
                'rating': avg_rating,
                'reviews': review_count,
            })
        
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
def flash_sale_api(request):
    """Get all flash sale products for frontend"""
    try:
        all_products = Product.objects.all().order_by('-created_at')
        products = [p for p in all_products if p.is_active and p.is_flash_sale]

        products_data = []
        for product in products:
            main_image = product.get_main_image()
            if not main_image:
                main_image = '/static/images/placeholder.jpg'

            try:
                regular_price = float(str(product.price))
            except (ValueError, TypeError):
                regular_price = 0.0

            # Use flash_sale_price if set, otherwise use regular price
            try:
                flash_price = float(str(product.flash_sale_price)) if product.flash_sale_price else None
            except (ValueError, TypeError):
                flash_price = None

            # If flash sale price is set, use it as price and regular price as compare_price
            if flash_price:
                price = flash_price
                compare_price = regular_price
            else:
                price = regular_price
                try:
                    compare_price = float(str(product.compare_price)) if product.compare_price else None
                except (ValueError, TypeError):
                    compare_price = None

            product_reviews = Review.objects.filter(product=product, status='approved')
            review_count = product_reviews.count()
            avg_rating = 0
            if review_count > 0:
                total_rating = sum([r.rating for r in product_reviews])
                avg_rating = round(total_rating / review_count, 1)

            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': price,
                'compare_price': compare_price,
                'category': product.category.name if product.category else 'Uncategorized',
                'stock': product.stock_quantity,
                'stock_status': product.stock_status,
                'image': main_image,
                'sku': product.sku,
                'rating': avg_rating,
                'reviews': review_count,
                'is_flash_sale': True,
            })

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
def categories_api(request):
    """Get all categories for frontend"""
    try:
        categories = Category.objects.all().order_by('name')
        
        categories_data = []
        for category in categories:
            # Workaround for Djongo bug - filter in Python
            all_products = Product.objects.filter(category=category)
            product_count = len([p for p in all_products if p.is_active])
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'product_count': product_count,
            })
        
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
def product_detail_api(request, product_id):
    """Get single product details"""
    try:
        # Workaround for Djongo bug - get by id then check is_active
        product = Product.objects.get(id=product_id)
        if not product.is_active:
            raise Product.DoesNotExist
        
        # Get the main image from ProductImage model
        main_image = product.get_main_image()
        if not main_image:
            main_image = '/static/images/placeholder.jpg'
        
        # Handle Decimal128 from MongoDB
        try:
            regular_price = float(str(product.price))
        except (ValueError, TypeError):
            regular_price = 0.0

        # Get compare_price (special price)
        try:
            special_price = float(str(product.compare_price)) if product.compare_price else None
        except (ValueError, TypeError):
            special_price = None

        # Get flash_sale_price if product is in flash sale
        try:
            flash_price = float(str(product.flash_sale_price)) if product.is_flash_sale and product.flash_sale_price else None
        except (ValueError, TypeError):
            flash_price = None

        # Determine display price and compare price
        if flash_price:
            # Flash sale: show flash price, strikethrough special price or regular price
            price = flash_price
            compare_price = special_price if special_price else regular_price
        elif special_price:
            # No flash sale but has special price: show special price, strikethrough regular
            price = special_price
            compare_price = regular_price
        else:
            # Just regular price
            price = regular_price
            compare_price = None

        # Get actual rating and review count
        product_reviews = Review.objects.filter(product=product, status='approved')
        review_count = product_reviews.count()
        avg_rating = 0
        if review_count > 0:
            total_rating = sum([r.rating for r in product_reviews])
            avg_rating = round(total_rating / review_count, 1)

        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': price,
            'compare_price': compare_price,
            'category': product.category.name if product.category else 'Uncategorized',
            'category_id': product.category.id if product.category else None,
            'stock': product.stock_quantity,
            'stock_status': product.stock_status,
            'image': main_image,
            'sku': product.sku,
            'rating': avg_rating,
            'reviews': review_count,
            'is_flash_sale': product.is_flash_sale,
        }
        
        return JsonResponse({
            'success': True,
            'product': product_data
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
