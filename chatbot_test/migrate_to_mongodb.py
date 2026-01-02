"""
Migration Script: SQLite to MongoDB
Copies all products, categories, and images from Django SQLite to MongoDB
"""

import os
import sys

# Add the backend to path so we can use Django models
BACKEND_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, BACKEND_PATH)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
import django
django.setup()

from products.models import Product, Category, ProductImage
from pymongo import MongoClient
from datetime import datetime

# MongoDB connection
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "ovn_store"

def migrate_to_mongodb():
    """Migrate all data from SQLite to MongoDB"""

    print("=" * 50)
    print("SQLITE TO MONGODB MIGRATION")
    print("=" * 50)

    # Connect to MongoDB
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        print(f"Connected to MongoDB: {DATABASE_NAME}")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return False

    # Get collections
    categories_col = db['categories']
    products_col = db['products']

    # Clear existing data
    print("\nClearing existing MongoDB data...")
    categories_col.delete_many({})
    products_col.delete_many({})
    print("Cleared existing collections")

    # Migrate Categories
    print("\n--- Migrating Categories ---")
    categories = Category.objects.all()
    category_map = {}  # Map Django ID to MongoDB ID

    for cat in categories:
        cat_doc = {
            "django_id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description or "",
            "image": cat.image.url if cat.image else "",
            "is_active": cat.is_active,
            "created_at": cat.created_at.isoformat() if cat.created_at else datetime.now().isoformat(),
            "updated_at": cat.updated_at.isoformat() if cat.updated_at else datetime.now().isoformat(),
        }
        result = categories_col.insert_one(cat_doc)
        category_map[cat.id] = result.inserted_id
        print(f"  Migrated category: {cat.name}")

    print(f"Total categories migrated: {len(category_map)}")

    # Migrate Products
    print("\n--- Migrating Products ---")
    products = Product.objects.filter(is_active=True)
    product_count = 0

    for product in products:
        # Get all images for this product
        images = []
        for img in product.images.all():
            images.append({
                "url": img.image.url if img.image else "",
                "alt_text": img.alt_text or product.name,
                "is_main": img.is_main,
            })

        # Get main image
        main_image = product.get_main_image() or ""

        product_doc = {
            "django_id": product.id,
            "name": product.name,
            "slug": product.slug,
            "description": product.description or "",
            "short_description": product.short_description or "",
            "category_id": category_map.get(product.category_id),
            "category_name": product.category.name if product.category else "General",
            "price": float(product.price),
            "compare_price": float(product.compare_price) if product.compare_price else 0,
            "cost_price": float(product.cost_price) if product.cost_price else 0,
            "sku": product.sku or "",
            "stock_quantity": product.stock_quantity or 0,
            "stock_status": product.stock_status,
            "is_active": product.is_active,
            "is_featured": product.is_featured,
            "is_flash_sale": product.is_flash_sale,
            "flash_sale_price": float(product.flash_sale_price) if product.flash_sale_price else None,
            "main_image": main_image,
            "images": images,
            "created_at": product.created_at.isoformat() if product.created_at else datetime.now().isoformat(),
            "updated_at": product.updated_at.isoformat() if product.updated_at else datetime.now().isoformat(),
        }

        products_col.insert_one(product_doc)
        product_count += 1
        print(f"  Migrated product: {product.name[:50]}... (Image: {main_image[:30] if main_image else 'None'}...)")

    print(f"\nTotal products migrated: {product_count}")

    # Verify migration
    print("\n--- Verification ---")
    mongo_categories = categories_col.count_documents({})
    mongo_products = products_col.count_documents({})
    print(f"MongoDB Categories: {mongo_categories}")
    print(f"MongoDB Products: {mongo_products}")

    print("\n" + "=" * 50)
    print("MIGRATION COMPLETE!")
    print("=" * 50)

    client.close()
    return True


if __name__ == "__main__":
    migrate_to_mongodb()
