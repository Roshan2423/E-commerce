#!/usr/bin/env python3
"""
One-Click Start Script for Django E-Commerce Platform
This script will check everything and start your e-commerce platform
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_command(command, cwd=None, capture_output=True, timeout=30):
    """Run a command with timeout"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                                  capture_output=True, text=True, timeout=timeout)
            return True, result.stdout
        else:
            result = subprocess.run(command, shell=True, cwd=cwd, check=True, timeout=timeout)
            return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr if capture_output else str(e)
    except subprocess.TimeoutExpired:
        return False, "Command timed out"


def check_mongodb():
    """Check if MongoDB is running"""
    print("🔍 Checking MongoDB connection...")
    try:
        import pymongo
        client = pymongo.MongoClient('localhost', 27017, serverSelectionTimeoutMS=3000)
        client.admin.command('ismaster')
        print("✅ MongoDB is running!")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("💡 Start MongoDB first:")
        print("   Windows: net start MongoDB OR mongod")
        print("   Mac: brew services start mongodb-community")
        print("   Linux: sudo systemctl start mongod")
        return False


def check_dependencies():
    """Check if all Python dependencies are installed"""
    print("📦 Checking Python dependencies...")
    
    required_packages = ['django', 'djongo', 'pymongo', 'pillow']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {missing_packages}")
        print("💡 Install with: cd backend && pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies installed!")
        return True


def setup_if_needed():
    """Setup database if migrations are missing"""
    backend_dir = Path(__file__).resolve().parent / "backend"
    
    # Check if migrations exist
    migrations_exist = any((backend_dir / app / "migrations").exists() 
                          for app in ["accounts", "products", "orders"])
    
    if not migrations_exist:
        print("🔧 Setting up database for first time...")
        success, output = run_command("python setup_database.py", Path(__file__).resolve().parent)
        if not success:
            print(f"❌ Database setup failed: {output}")
            return False
        print("✅ Database setup completed!")
    
    return True


def start_server():
    """Start the Django development server"""
    print("🚀 Starting Django development server...")
    backend_dir = Path(__file__).resolve().parent / "backend"
    
    try:
        print("🌐 Server will start at: http://localhost:8000")
        print("📊 Admin Dashboard: http://localhost:8000/dashboard/")
        print("⚙️  Django Admin: http://localhost:8000/admin/")
        print("🛑 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the server (non-capturing to show live output)
        subprocess.run("python manage.py runserver", shell=True, cwd=backend_dir, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        return False
    
    return True


def main():
    """Main startup function"""
    print("🚀 Django E-Commerce Platform Startup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('backend'):
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)
    
    # Step 1: Check MongoDB
    if not check_mongodb():
        sys.exit(1)
    
    # Step 2: Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Step 3: Setup if needed
    if not setup_if_needed():
        sys.exit(1)
    
    # Step 4: Start the server
    print("\n🎉 Everything looks good! Starting the server...")
    time.sleep(1)
    
    start_server()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Startup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("\n📋 Manual startup steps:")
        print("   1. Make sure MongoDB is running")
        print("   2. cd backend")
        print("   3. pip install -r requirements.txt")
        print("   4. python manage.py runserver")