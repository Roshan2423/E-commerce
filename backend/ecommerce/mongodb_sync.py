"""
MongoDB Sync Module
Automatically syncs all Django data to MongoDB using signals.
All CRUD operations on Products, Orders, Categories, Users, etc.
are automatically mirrored to MongoDB.
"""

from pymongo import MongoClient
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "ovn_store"

# Global MongoDB connection
_client = None
_db = None


def get_db():
    """Get MongoDB database connection"""
    global _client, _db
    if _db is None:
        try:
            _client = MongoClient(MONGO_URI)
            _db = _client[DATABASE_NAME]
            logger.info("Connected to MongoDB successfully!")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return None
    return _db


def sync_category(category, deleted=False):
    """Sync a Category to MongoDB"""
    db = get_db()
    if not db:
        return

    try:
        if deleted:
            db.categories.delete_one({"django_id": category.id})
            print(f"[MongoDB] Deleted category: {category.name}")
        else:
            doc = {
                "django_id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description or "",
                "image": category.image.url if category.image else "",
                "is_active": category.is_active,
                "created_at": category.created_at.isoformat() if category.created_at else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            db.categories.update_one(
                {"django_id": category.id},
                {"$set": doc},
                upsert=True
            )
            print(f"[MongoDB] Synced category: {category.name}")
    except Exception as e:
        logger.error(f"Error syncing category: {e}")


def sync_product(product, deleted=False):
    """Sync a Product to MongoDB"""
    db = get_db()
    if not db:
        return

    try:
        if deleted:
            db.products.delete_one({"django_id": product.id})
            print(f"[MongoDB] Deleted product: {product.name}")
        else:
            # Get all images for this product
            images = []
            try:
                for img in product.images.all():
                    images.append({
                        "url": img.image.url if img.image else "",
                        "alt_text": img.alt_text or product.name,
                        "is_main": img.is_main,
                    })
            except:
                pass

            # Get main image
            main_image = ""
            try:
                main_image = product.get_main_image() or ""
            except:
                pass

            # Calculate average rating from approved reviews
            avg_rating = 0
            review_count = 0
            try:
                from django.db.models import Avg
                reviews = product.reviews.filter(status='approved')
                review_count = reviews.count()
                if review_count > 0:
                    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            except:
                pass

            doc = {
                "django_id": product.id,
                "name": product.name,
                "slug": product.slug,
                "description": product.description or "",
                "short_description": product.short_description or "",
                "category_id": product.category_id,
                "category_name": product.category.name if product.category else "General",
                "price": float(product.price),
                "compare_price": float(product.compare_price) if product.compare_price else 0,
                "cost_price": float(product.cost_price) if product.cost_price else 0,
                "sku": product.sku or "",
                "stock_quantity": product.stock_quantity or 0,
                "stock_status": product.stock_status,
                "is_active": product.is_active,
                "is_featured": product.is_featured,
                "is_flash_sale": getattr(product, 'is_flash_sale', False),
                "flash_sale_price": float(product.flash_sale_price) if getattr(product, 'flash_sale_price', None) else None,
                "main_image": main_image,
                "images": images,
                "avg_rating": round(avg_rating, 1),
                "review_count": review_count,
                "created_at": product.created_at.isoformat() if product.created_at else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            db.products.update_one(
                {"django_id": product.id},
                {"$set": doc},
                upsert=True
            )
            print(f"[MongoDB] Synced product: {product.name}")
    except Exception as e:
        logger.error(f"Error syncing product: {e}")


def sync_product_image(product_image, deleted=False):
    """Sync ProductImage changes - update the parent product"""
    try:
        if product_image.product:
            sync_product(product_image.product)
    except Exception as e:
        logger.error(f"Error syncing product image: {e}")


def sync_order(order, deleted=False):
    """Sync an Order to MongoDB"""
    db = get_db()
    if not db:
        return

    try:
        # Get order number (use method or UUID)
        order_number = order.get_order_number() if hasattr(order, 'get_order_number') else str(order.order_id)[:8].upper()

        if deleted:
            db.orders.delete_one({"django_id": order.id})
            print(f"[MongoDB] Deleted order: {order_number}")
        else:
            # Get order items
            items = []
            try:
                for item in order.items.all():
                    items.append({
                        "product_id": item.product_id,
                        "product_name": getattr(item, 'product_name', '') or (item.product.name if item.product else "Unknown"),
                        "product_sku": getattr(item, 'product_sku', ''),
                        "quantity": item.quantity,
                        "unit_price": float(item.unit_price) if hasattr(item, 'unit_price') else 0,
                        "total_price": float(item.total_price) if hasattr(item, 'total_price') else 0,
                    })
            except Exception as e:
                print(f"Error getting order items: {e}")

            doc = {
                "django_id": order.id,
                "order_id": str(order.order_id),
                "order_number": order_number,
                "user_id": order.user_id if order.user_id else None,
                "user_email": order.user.email if order.user else getattr(order, 'guest_email', ''),
                "is_guest_order": getattr(order, 'is_guest_order', False),
                "guest_email": getattr(order, 'guest_email', ''),
                "status": order.status,
                "payment_status": getattr(order, 'payment_status', 'pending'),
                "payment_method": getattr(order, 'payment_method', ''),
                "payment_transaction_id": getattr(order, 'payment_transaction_id', ''),
                "subtotal": float(order.subtotal) if hasattr(order, 'subtotal') else 0,
                "shipping_cost": float(order.shipping_cost) if hasattr(order, 'shipping_cost') else 0,
                "tax_amount": float(order.tax_amount) if hasattr(order, 'tax_amount') else 0,
                "discount_amount": float(order.discount_amount) if hasattr(order, 'discount_amount') else 0,
                "total_amount": float(order.total_amount) if hasattr(order, 'total_amount') else 0,
                "shipping_address": getattr(order, 'shipping_address', ''),
                "billing_address": getattr(order, 'billing_address', ''),
                "shipping_method": getattr(order, 'shipping_method', ''),
                "tracking_number": getattr(order, 'tracking_number', ''),
                "notes": getattr(order, 'notes', ''),
                "items": items,
                "is_deleted": getattr(order, 'is_deleted', False),
                "created_at": order.created_at.isoformat() if hasattr(order, 'created_at') and order.created_at else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "shipped_at": order.shipped_at.isoformat() if hasattr(order, 'shipped_at') and order.shipped_at else None,
                "delivered_at": order.delivered_at.isoformat() if hasattr(order, 'delivered_at') and order.delivered_at else None,
            }
            db.orders.update_one(
                {"django_id": order.id},
                {"$set": doc},
                upsert=True
            )
            print(f"[MongoDB] Synced order: {order_number}")
    except Exception as e:
        print(f"Error syncing order: {e}")
        logger.error(f"Error syncing order: {e}")


def sync_order_item(order_item, deleted=False):
    """Sync OrderItem changes - update the parent order"""
    try:
        if order_item.order:
            sync_order(order_item.order)
    except Exception as e:
        logger.error(f"Error syncing order item: {e}")


def sync_user(user, deleted=False):
    """Sync a User to MongoDB"""
    db = get_db()
    if not db:
        return

    try:
        if deleted:
            db.users.delete_one({"django_id": user.id})
            print(f"[MongoDB] Deleted user: {user.email}")
        else:
            doc = {
                "django_id": user.id,
                "email": user.email,
                "username": getattr(user, 'username', user.email),
                "first_name": getattr(user, 'first_name', ''),
                "last_name": getattr(user, 'last_name', ''),
                "phone": getattr(user, 'phone', ''),
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "date_joined": user.date_joined.isoformat() if hasattr(user, 'date_joined') and user.date_joined else datetime.now().isoformat(),
                "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None,
                "updated_at": datetime.now().isoformat(),
            }
            db.users.update_one(
                {"django_id": user.id},
                {"$set": doc},
                upsert=True
            )
            print(f"[MongoDB] Synced user: {user.email}")
    except Exception as e:
        logger.error(f"Error syncing user: {e}")


def sync_review(review, deleted=False):
    """Sync a Review to MongoDB"""
    db = get_db()
    if not db:
        return

    try:
        if deleted:
            db.reviews.delete_one({"django_id": review.id})
            print(f"[MongoDB] Deleted review: {review.id}")
        else:
            doc = {
                "django_id": review.id,
                "product_id": review.product_id,
                "product_name": review.product.name if review.product else "",
                "user_id": review.user_id,
                "user_email": review.user.email if review.user else "",
                "rating": review.rating,
                "title": getattr(review, 'title', ''),
                "comment": review.comment,
                "status": getattr(review, 'status', 'pending'),
                "is_verified_purchase": getattr(review, 'is_verified_purchase', False),
                "created_at": review.created_at.isoformat() if hasattr(review, 'created_at') and review.created_at else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            db.reviews.update_one(
                {"django_id": review.id},
                {"$set": doc},
                upsert=True
            )
            print(f"[MongoDB] Synced review: {review.id}")
    except Exception as e:
        logger.error(f"Error syncing review: {e}")


def sync_contact(contact, deleted=False):
    """Sync a Contact message to MongoDB"""
    db = get_db()
    if not db:
        return

    try:
        if deleted:
            db.contacts.delete_one({"django_id": contact.id})
            print(f"[MongoDB] Deleted contact: {contact.id}")
        else:
            doc = {
                "django_id": contact.id,
                "name": getattr(contact, 'name', ''),
                "email": getattr(contact, 'email', ''),
                "phone": getattr(contact, 'phone', ''),
                "subject": getattr(contact, 'subject', ''),
                "message": getattr(contact, 'message', ''),
                "is_read": getattr(contact, 'is_read', False),
                "created_at": contact.created_at.isoformat() if hasattr(contact, 'created_at') and contact.created_at else datetime.now().isoformat(),
            }
            db.contacts.update_one(
                {"django_id": contact.id},
                {"$set": doc},
                upsert=True
            )
            print(f"[MongoDB] Synced contact: {contact.id}")
    except Exception as e:
        logger.error(f"Error syncing contact: {e}")


def full_sync():
    """Full sync of all data from Django to MongoDB"""
    from products.models import Product, Category, ProductImage
    from orders.models import Order
    from django.contrib.auth import get_user_model

    User = get_user_model()

    print("\n" + "=" * 50)
    print("FULL MONGODB SYNC")
    print("=" * 50)

    db = get_db()
    if not db:
        print("Failed to connect to MongoDB!")
        return

    # Sync Categories
    print("\n--- Syncing Categories ---")
    for cat in Category.objects.all():
        sync_category(cat)

    # Sync Products
    print("\n--- Syncing Products ---")
    for product in Product.objects.all():
        sync_product(product)

    # Sync Orders
    print("\n--- Syncing Orders ---")
    for order in Order.objects.all():
        sync_order(order)

    # Sync Users
    print("\n--- Syncing Users ---")
    for user in User.objects.all():
        sync_user(user)

    # Try to sync Reviews if model exists
    try:
        from products.models import Review
        print("\n--- Syncing Reviews ---")
        for review in Review.objects.all():
            sync_review(review)
    except:
        pass

    # Try to sync Contacts if model exists
    try:
        from contacts.models import Contact
        print("\n--- Syncing Contacts ---")
        for contact in Contact.objects.all():
            sync_contact(contact)
    except:
        pass

    print("\n" + "=" * 50)
    print("SYNC COMPLETE!")
    print("=" * 50)
