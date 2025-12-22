#!/usr/bin/env python3
"""
Database connectivity check for Django E-Commerce Platform
Run this to verify your MongoDB setup before running migrations
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line


def test_database_connection():
    """Test Django database connection"""
    print("🔍 Testing Django-MongoDB connection...")
    
    try:
        # Test the connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Django successfully connected to MongoDB!")
        return True
    except Exception as e:
        print(f"❌ Django-MongoDB connection failed: {e}")
        print("\n🔧 Possible solutions:")
        print("   1. Make sure MongoDB is running")
        print("   2. Check MONGODB_HOST and MONGODB_PORT in .env")
        print("   3. Verify djongo is installed: pip install djongo==1.3.6")
        print("   4. Check if pymongo is installed: pip install pymongo==4.6.0")
        return False


def check_models():
    """Check if models can be imported"""
    print("\n📋 Checking Django models...")
    
    try:
        from accounts.models import User, Address
        from products.models import Product, Category, ProductImage
        from orders.models import Order, OrderItem
        print("✅ All models imported successfully!")
        return True
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False


def run_migrations_check():
    """Check if migrations are needed"""
    print("\n🔄 Checking migration status...")
    
    try:
        from django.core.management import call_command
        from django.core.management.base import CommandError
        
        # Check for unapplied migrations
        call_command('showmigrations', verbosity=0)
        print("✅ Migration system is working!")
        
        print("\n📝 To create and apply migrations, run:")
        print("   python manage.py makemigrations")
        print("   python manage.py migrate")
        
        return True
    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        return False


def main():
    """Main check function"""
    print("🧪 Database Connection Test")
    print("=" * 30)
    
    success = True
    
    # Test database connection
    if not test_database_connection():
        success = False
    
    # Check models
    if not check_models():
        success = False
    
    # Check migrations
    if not run_migrations_check():
        success = False
    
    if success:
        print("\n🎉 All checks passed! Your database setup is ready.")
        print("\n📋 Ready to run:")
        print("   python manage.py makemigrations")
        print("   python manage.py migrate")
        print("   python manage.py createsuperuser")
        print("   python manage.py runserver")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")


if __name__ == "__main__":
    main()