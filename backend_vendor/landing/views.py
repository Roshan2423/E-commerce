from django.shortcuts import render


def landing_page(request):
    """Main SaaS landing page"""
    return render(request, 'landing/index.html')
