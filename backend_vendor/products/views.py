from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.db import models
from .models import Product, Category, ProductImage, ProductVariant, Review, ReviewImage
from .forms import ProductForm, CategoryForm, ProductImageForm
from ecommerce.mixins import AdminRequiredMixin
from ecommerce.utils import process_uploaded_images, is_admin_user


def product_list_view(request):
    """Simple function-based view to avoid ListView complexity"""
    # Check if user is admin
    if not (request.user.is_staff or request.user.is_superuser):
        from django.contrib.auth.decorators import login_required
        from django.http import HttpResponseForbidden
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('accounts:login')
        return HttpResponseForbidden()
    
    context = {
        'products': [],
        'categories': [],
        'search': '',
        'selected_category': '',
        'selected_stock_status': '',
        'selected_is_active': '',
    }
    
    try:
        # Get all products as a simple list
        products = list(Product.objects.all())
        context['products'] = products
        print(f"Loaded {len(products)} products successfully")
        
        # Get all categories
        categories = list(Category.objects.all())
        context['categories'] = categories
        print(f"Loaded {len(categories)} categories successfully")
        
    except Exception as e:
        print(f"Error loading products: {e}")
        import traceback
        traceback.print_exc()
        # Keep empty lists as defaults
        
    return render(request, 'admin/products/list.html', context)


def product_detail_view(request, pk):
    """Simple function-based view for product details"""
    # Check if user is admin
    if not (request.user.is_staff or request.user.is_superuser):
        from django.http import HttpResponseForbidden
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('accounts:login')
        return HttpResponseForbidden()
    
    try:
        product = Product.objects.get(pk=pk)
        
        context = {
            'product': product,
            'images': [],
            'variants': [],
        }
        
        try:
            context['images'] = list(product.images.all())
            context['variants'] = list(product.variants.all())
        except Exception as e:
            print(f"Error loading related objects: {e}")
            # Keep empty lists as defaults
            
        return render(request, 'admin/products/detail.html', context)
        
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')
        return redirect('products:list')
    except Exception as e:
        print(f"Error loading product {pk}: {e}")
        messages.error(request, 'Error loading product.')
        return redirect('products:list')


class ProductCreateView(AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'admin/products/form.html'
    success_url = reverse_lazy('products:list')
    
    def form_valid(self, form):
        print(f"DEBUG: Form is valid, creating product...")
        print(f"DEBUG: Form data: {form.cleaned_data}")
        print(f"DEBUG: POST data keys: {list(self.request.POST.keys())}")
        
        try:
            # Save the product first
            response = super().form_valid(form)
            print(f"DEBUG: Product saved successfully - ID: {self.object.id}")
            print(f"DEBUG: Product name: {self.object.name}")
            print(f"DEBUG: Product SKU: {self.object.sku}")
            
            # Process uploaded images
            self.handle_uploaded_images()
            
            messages.success(self.request, 'Product created successfully!')
            print(f"DEBUG: Success message added, redirecting...")
            return response
        except Exception as e:
            print(f"ERROR: Failed to save product: {e}")
            import traceback
            traceback.print_exc()
            messages.error(self.request, f'Error creating product: {str(e)}')
            return super().form_invalid(form)
    
    def form_invalid(self, form):
        print(f"DEBUG: Form is invalid!")
        print(f"DEBUG: Form errors: {form.errors}")
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def handle_uploaded_images(self):
        """Process images from the JavaScript upload system"""
        process_uploaded_images(self.request, self.object, ProductImage)




class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'admin/products/form.html'
    success_url = reverse_lazy('products:list')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            
            # Handle deletion of existing images
            self.process_image_deletions()
            
            # Process uploaded images
            process_uploaded_images(self.request, self.object, ProductImage)

            messages.success(self.request, 'Product updated successfully!')
            return response
        except Exception as e:
            print(f"ERROR: Failed to update product: {e}")
            import traceback
            traceback.print_exc()
            messages.error(self.request, f'Error updating product: {str(e)}')
            return super().form_invalid(form)

    def process_image_deletions(self):
        """Delete images marked for deletion"""
        delete_fields = [key for key in self.request.POST.keys() if key.startswith('delete_image_')]
        print(f"DEBUG: Found {len(delete_fields)} images to delete: {delete_fields}")

        for field_name in delete_fields:
            try:
                image_id = int(field_name.replace('delete_image_', ''))
                deleted = ProductImage.objects.filter(id=image_id, product=self.object).delete()
                print(f"DEBUG: Deleted image {image_id}: {deleted}")
            except (ValueError, ProductImage.DoesNotExist) as e:
                print(f"DEBUG: Error deleting image: {e}")


class ProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'admin/products/confirm_delete.html'
    success_url = reverse_lazy('products:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Product deleted successfully!')
        return super().delete(request, *args, **kwargs)


class CategoryListView(AdminRequiredMixin, ListView):
    model = Category
    template_name = 'admin/products/categories.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        try:
            # Simplified query without complex aggregation
            categories = list(Category.objects.all())
            return categories
        except Exception as e:
            print(f"Error loading categories: {e}")
            return []


class CategoryCreateView(AdminRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'admin/products/category_form.html'
    success_url = reverse_lazy('products:categories')
    
    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)


class CategoryUpdateView(AdminRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'admin/products/category_form.html'
    success_url = reverse_lazy('products:categories')
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)


@login_required
@user_passes_test(is_admin_user)
def delete_category(request, pk):
    """Direct category deletion without confirmation page"""
    category = get_object_or_404(Category, pk=pk)

    # Check if category has products
    if category.products.count() > 0:
        messages.error(request, f'Cannot delete "{category.name}" because it has {category.products.count()} products. Please move or delete the products first.')
    else:
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')

    return redirect('products:categories')


# ============ Flash Sale Admin Views ============

@login_required
@user_passes_test(is_admin_user)
def flash_sale_view(request):
    """Manage flash sale products"""
    context = {
        'products': [],
        'flash_sale_products': [],
    }

    try:
        all_products = list(Product.objects.filter(is_active=True))
        flash_sale_products = [p for p in all_products if p.is_flash_sale]
        non_flash_products = [p for p in all_products if not p.is_flash_sale]

        context['products'] = non_flash_products
        context['flash_sale_products'] = flash_sale_products

    except Exception as e:
        print(f"Error loading flash sale products: {e}")
        messages.error(request, f'Error loading products: {str(e)}')

    return render(request, 'admin/products/flash_sale.html', context)


@login_required
@user_passes_test(is_admin_user)
def toggle_flash_sale(request, pk):
    """Toggle flash sale status for a product"""
    product = get_object_or_404(Product, pk=pk)
    product.is_flash_sale = not product.is_flash_sale

    # Clear flash sale price when removing from flash sale
    if not product.is_flash_sale:
        product.flash_sale_price = None

    product.save()
    return redirect('products:flash_sale')


@login_required
@user_passes_test(is_admin_user)
def update_flash_price(request, pk):
    """Update flash sale price for a product"""
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        flash_price = request.POST.get('flash_sale_price', '').strip()

        if flash_price:
            try:
                product.flash_sale_price = float(flash_price)
                product.save()
            except ValueError:
                pass
        else:
            product.flash_sale_price = None
            product.save()

    return redirect('products:flash_sale')


# ============ Review Admin Views ============

@login_required
@user_passes_test(is_admin_user)
def review_list_view(request):
    """List all reviews with filtering"""
    context = {
        'reviews': [],
        'selected_status': request.GET.get('status', ''),
        'selected_rating': request.GET.get('rating', ''),
        'search': request.GET.get('search', ''),
    }

    try:
        reviews = list(Review.objects.select_related('product', 'user', 'order').all())

        # Filter by status
        if context['selected_status']:
            reviews = [r for r in reviews if r.status == context['selected_status']]

        # Filter by rating
        if context['selected_rating']:
            try:
                rating_val = int(context['selected_rating'])
                reviews = [r for r in reviews if r.rating == rating_val]
            except ValueError:
                pass

        # Search by product name or user
        if context['search']:
            search_term = context['search'].lower()
            reviews = [r for r in reviews if
                       search_term in r.product.name.lower() or
                       search_term in r.user.username.lower() or
                       (r.user.first_name and search_term in r.user.first_name.lower())]

        context['reviews'] = reviews
        context['pending_count'] = len([r for r in Review.objects.all() if r.status == 'pending'])

    except Exception as e:
        print(f"Error loading reviews: {e}")
        import traceback
        traceback.print_exc()

    return render(request, 'admin/reviews/list.html', context)


@login_required
@user_passes_test(is_admin_user)
def review_detail_view(request, pk):
    """View single review details"""
    try:
        review = Review.objects.select_related('product', 'user', 'order').get(pk=pk)
        images = list(review.images.all())

        context = {
            'review': review,
            'images': images,
        }

        return render(request, 'admin/reviews/detail.html', context)

    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
        return redirect('products:reviews')
    except Exception as e:
        print(f"Error loading review {pk}: {e}")
        messages.error(request, 'Error loading review.')
        return redirect('products:reviews')


@login_required
@user_passes_test(is_admin_user)
def review_update_view(request, pk):
    """Update review status and admin response"""
    try:
        review = Review.objects.select_related('product', 'user', 'order').get(pk=pk)

        if request.method == 'POST':
            new_status = request.POST.get('status')
            admin_response = request.POST.get('admin_response', '').strip()

            if new_status in ['pending', 'approved', 'rejected']:
                review.status = new_status

            review.admin_response = admin_response if admin_response else None
            review.save()

            messages.success(request, 'Review updated successfully!')
            return redirect('products:reviews')

        context = {
            'review': review,
            'images': list(review.images.all()),
        }

        return render(request, 'admin/reviews/edit.html', context)

    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
        return redirect('products:reviews')
    except Exception as e:
        print(f"Error updating review {pk}: {e}")
        messages.error(request, 'Error updating review.')
        return redirect('products:reviews')


@login_required
@user_passes_test(is_admin_user)
def review_delete_view(request, pk):
    """Delete a review"""
    try:
        review = Review.objects.get(pk=pk)

        if request.method == 'POST':
            review.delete()
            messages.success(request, 'Review deleted successfully!')
            return redirect('products:reviews')

        context = {
            'review': review,
        }

        return render(request, 'admin/reviews/confirm_delete.html', context)

    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
        return redirect('products:reviews')
    except Exception as e:
        print(f"Error deleting review {pk}: {e}")
        messages.error(request, 'Error deleting review.')
        return redirect('products:reviews')


@login_required
@user_passes_test(is_admin_user)
def review_quick_action(request, pk, action):
    """Quick approve/reject action for reviews"""
    try:
        review = Review.objects.get(pk=pk)

        if action == 'approve':
            review.status = 'approved'
            review.save()
            messages.success(request, 'Review approved!')
        elif action == 'reject':
            review.status = 'rejected'
            review.save()
            messages.success(request, 'Review rejected!')
        else:
            messages.error(request, 'Invalid action.')

        return redirect('products:reviews')

    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
        return redirect('products:reviews')