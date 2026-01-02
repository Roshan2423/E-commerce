#!/usr/bin/env python
"""
OVN Store - Single Server Startup Script
Runs the Django development server serving both frontend and backend.
"""

import os
import sys
import subprocess

def main():
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    os.chdir(backend_dir)

    print("=" * 50)
    print("  OVN Store - E-Commerce Platform")
    print("=" * 50)
    print()
    print("Starting server...")
    print()
    print("  Store:     http://127.0.0.1:8000/")
    print("  Admin:     http://127.0.0.1:8000/dashboard/")
    print("  API:       http://127.0.0.1:8000/api/")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    print()

    # Run Django development server
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000'
        ], check=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
