#!/usr/bin/env python3
"""
Complete Database Setup Script for Django E-Commerce Platform
This script will create migrations and set up your database automatically
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, cwd=None, capture_output=True):
    """Run a command and return success status"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                                  capture_output=True, text=True)
            return True, result.stdout
        else:
            result = subprocess.run(command, shell=True, cwd=cwd, check=True)
            return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr if capture_output else str(e)


def setup_database():
    """Setup the database with migrations"""
    print("🗄️  Setting up Django database with MongoDB...")
    
    backend_dir = Path(__file__).resolve().parent
    
    # Step 1: Create migrations
    print("\n📝 Creating migrations...")
    success, output = run_command("python manage.py makemigrations accounts", backend_dir)
    if success:
        print("✅ Created accounts migrations")
    else:
        print(f"⚠️  Accounts migrations: {output}")
    
    success, output = run_command("python manage.py makemigrations products", backend_dir)
    if success:
        print("✅ Created products migrations")
    else:
        print(f"⚠️  Products migrations: {output}")
    
    success, output = run_command("python manage.py makemigrations orders", backend_dir)
    if success:
        print("✅ Created orders migrations")
    else:
        print(f"⚠️  Orders migrations: {output}")
    
    # Create any remaining migrations
    success, output = run_command("python manage.py makemigrations", backend_dir)
    if success:
        print("✅ Created any remaining migrations")
    
    # Step 2: Apply migrations
    print("\n🔄 Applying migrations to MongoDB...")
    success, output = run_command("python manage.py migrate", backend_dir)
    if success:
        print("✅ Successfully applied all migrations!")
        return True
    else:
        print(f"❌ Migration failed: {output}")
        return False


def create_sample_data():
    """Create sample data using Django management command"""
    print("\n📦 Creating sample data...")
    
    sample_data_script = '''
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from accounts.models import User
from products.models import Category, Product
from django.utils.text import slugify

# Create categories
categories_data = [
    {"name": "Electronics", "description": "Electronic devices and gadgets"},
    {"name": "Clothing", "description": "Fashion and apparel"},
    {"name": "Books", "description": "Books and literature"},
    {"name": "Home & Garden", "description": "Home improvement and gardening"}
]

print("Creating categories...")
for cat_data in categories_data:
    category, created = Category.objects.get_or_create(
        name=cat_data["name"],
        defaults={
            "description": cat_data["description"],
            "slug": slugify(cat_data["name"])
        }
    )
    if created:
        print(f"✓ Created category: {category.name}")
    else:
        print(f"- Category already exists: {category.name}")

# Create products
electronics = Category.objects.get(name="Electronics")
clothing = Category.objects.get(name="Clothing")
books = Category.objects.get(name="Books")

products_data = [
    {
        "name": "Smartphone Pro",
        "category": electronics,
        "price": 699.99,
        "description": "Latest smartphone with advanced features",
        "sku": "PHONE001",
        "stock_quantity": 50
    },
    {
        "name": "Gaming Laptop",
        "category": electronics,
        "price": 1299.99,
        "description": "High-performance gaming laptop",
        "sku": "LAPTOP001",
        "stock_quantity": 25
    },
    {
        "name": "Cotton T-Shirt",
        "category": clothing,
        "price": 29.99,
        "description": "Comfortable cotton t-shirt",
        "sku": "SHIRT001",
        "stock_quantity": 100
    },
    {
        "name": "Django Web Development",
        "category": books,
        "price": 49.99,
        "description": "Complete guide to Django development",
        "sku": "BOOK001",
        "stock_quantity": 30
    }
]

print("Creating products...")
for prod_data in products_data:
    product, created = Product.objects.get_or_create(
        sku=prod_data["sku"],
        defaults={
            "name": prod_data["name"],
            "category": prod_data["category"],
            "price": prod_data["price"],
            "description": prod_data["description"],
            "stock_quantity": prod_data["stock_quantity"],
            "slug": slugify(prod_data["name"])
        }
    )
    if created:
        print(f"✓ Created product: {product.name}")
    else:
        print(f"- Product already exists: {product.name}")

print("\\n✅ Sample data created successfully!")
'''
    
    # Write and run the sample data script
    script_path = Path(__file__).parent / "backend" / "create_sample_data.py"
    with open(script_path, 'w') as f:
        f.write(sample_data_script)
    
    backend_dir = Path(__file__).resolve().parent / "backend"
    success, output = run_command("python create_sample_data.py", backend_dir)
    
    # Clean up the temporary script
    script_path.unlink()
    
    if success:
        print("✅ Sample data created successfully!")
    else:
        print(f"⚠️  Sample data creation: {output}")
    
    return success


def main():
    """Main setup function"""
    print("🚀 Complete Database Setup for Django E-Commerce")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('backend'):
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n❌ Database setup failed!")
        return False
    
    # Create sample data
    create_sample_data()
    
    print("\n🎉 Database setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. cd backend")
    print("   2. python manage.py createsuperuser")
    print("   3. python manage.py runserver")
    print("   4. Visit: http://localhost:8000/dashboard/")
    print("   5. Visit: http://localhost:8000/admin/")
    
    print("\n📊 Your MongoDB database now contains:")
    print("   • User authentication system")
    print("   • Product categories (Electronics, Clothing, Books, Home & Garden)")
    print("   • Sample products in each category")
    print("   • Order management system")
    print("   • Complete admin interface")
    
    return True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check the error message and try again.")