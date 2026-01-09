"""
Admin views for managing demo page settings
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q

from .models import DemoSettings
from products.models import Product, Category


def is_admin(user):
    """Check if user is admin/staff"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def demo_settings_view(request):
    """Admin view to manage demo page product selections"""
    settings = DemoSettings.get_settings()

    # Get all active products for selection
    all_products = Product.objects.filter(is_active=True).order_by('-created_at')
    all_categories = Category.objects.all().order_by('name')

    # Handle search/filter
    search = request.GET.get('search', '')
    if search:
        all_products = all_products.filter(
            Q(name__icontains=search) | Q(sku__icontains=search)
        )

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'save_settings':
            # Get selected product IDs from form
            featured_ids = request.POST.getlist('featured_products')
            flash_sale_ids = request.POST.getlist('flash_sale_products')
            new_arrival_ids = request.POST.getlist('new_arrival_products')
            all_demo_ids = request.POST.getlist('all_products')
            category_ids = request.POST.getlist('categories')

            # Update ManyToMany relationships
            settings.featured_products.set(featured_ids)
            settings.flash_sale_products.set(flash_sale_ids)
            settings.new_arrival_products.set(new_arrival_ids)
            settings.all_products.set(all_demo_ids)
            settings.categories.set(category_ids)

            settings.save()
            messages.success(request, 'Demo settings saved successfully!')
            return redirect('demo:demo_settings')

        elif action == 'clear_all':
            # Clear all selections
            settings.featured_products.clear()
            settings.flash_sale_products.clear()
            settings.new_arrival_products.clear()
            settings.all_products.clear()
            settings.categories.clear()
            settings.save()
            messages.success(request, 'All demo selections cleared. Demo will use fallback static data.')
            return redirect('demo:demo_settings')

    # Get currently selected IDs for template
    selected_featured = list(settings.featured_products.values_list('id', flat=True))
    selected_flash_sale = list(settings.flash_sale_products.values_list('id', flat=True))
    selected_new_arrivals = list(settings.new_arrival_products.values_list('id', flat=True))
    selected_all = list(settings.all_products.values_list('id', flat=True))
    selected_categories = list(settings.categories.values_list('id', flat=True))

    context = {
        'settings': settings,
        'all_products': all_products,
        'all_categories': all_categories,
        'selected_featured': selected_featured,
        'selected_flash_sale': selected_flash_sale,
        'selected_new_arrivals': selected_new_arrivals,
        'selected_all': selected_all,
        'selected_categories': selected_categories,
        'search': search,
        # Stats
        'total_products': all_products.count(),
        'featured_count': len(selected_featured),
        'flash_sale_count': len(selected_flash_sale),
        'new_arrivals_count': len(selected_new_arrivals),
        'all_count': len(selected_all),
        'categories_count': len(selected_categories),
    }

    return render(request, 'demo/admin/settings.html', context)
