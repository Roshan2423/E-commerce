from django.shortcuts import render


def index(request):
    """Main frontend view - serves the SPA"""
    return render(request, 'frontend/index.html')


def catch_all(request, path=''):
    """Catch-all view for SPA routing - all frontend routes go to index"""
    return render(request, 'frontend/index.html')
