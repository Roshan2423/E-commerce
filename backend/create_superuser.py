#!/usr/bin/env python3
"""
Quick Superuser Creation Script
Creates a default admin user for testing (change password after first login)
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

def create_test_superuser():
    """Create a test superuser for development"""
    try:
        # Try to create a test superuser
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        print("✅ Test superuser created successfully!")
        print("📧 Email: admin@example.com")
        print("🔑 Password: admin123")
        print("⚠️  Please change this password after first login!")
        return True
        
    except IntegrityError:
        print("ℹ️  Superuser already exists")
        print("📧 Try: admin@example.com")
        print("🔑 Password: admin123")
        return True
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        print("💡 Try manually: python manage.py createsuperuser")
        return False


if __name__ == "__main__":
    print("👑 Creating test superuser...")
    create_test_superuser()