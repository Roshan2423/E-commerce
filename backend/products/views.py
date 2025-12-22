from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.db import models
from .models import Product, Category, ProductImage, ProductVariant
from .forms import ProductForm, CategoryForm, ProductImageForm


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require admin/staff access"""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class ProductListView(AdminRequiredMixin, ListView):
    model = Product
    template_name = 'admin/products/list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        try:
            queryset = Product.objects.all()
            
            # Search functionality
            search = self.request.GET.get('search')
            if search:
                queryset = queryset.filter(name__icontains=search)
            
            # Category filter
            category = self.request.GET.get('category')
            if category:
                queryset = queryset.filter(category__id=category)
            
            return queryset.order_by('-id')
        except:
            return Product.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['categories'] = Category.objects.all()
        except:
            context['categories'] = []
        context['search'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_stock_status'] = self.request.GET.get('stock_status', '')
        context['selected_is_active'] = self.request.GET.get('is_active', '')
        return context


class ProductDetailView(AdminRequiredMixin, DetailView):
    model = Product
    template_name = 'admin/products/detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = self.object.images.all()
        context['variants'] = self.object.variants.all()
        return context


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
            self.process_uploaded_images()
            
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
    
    def process_uploaded_images(self):
        """Process images from the JavaScript upload system"""
        import json
        import base64
        from django.core.files.base import ContentFile
        from io import BytesIO
        
        print(f"DEBUG: Processing images for product {self.object.name}")
        
        # Look for image_data_* fields in POST data
        image_data_fields = [key for key in self.request.POST.keys() if key.startswith('image_data_')]
        print(f"DEBUG: Found image fields: {image_data_fields}")
        
        for field_name in image_data_fields:
            try:
                image_data_json = self.request.POST.get(field_name)
                print(f"DEBUG: Processing {field_name}")
                
                if image_data_json:
                    image_data = json.loads(image_data_json)
                    print(f"DEBUG: Image data keys: {image_data.keys()}")
                    
                    # Extract base64 data (format: data:image/jpeg;base64,/9j/4AAQ...)
                    image_src = image_data.get('src', '')
                    if image_src.startswith('data:image'):
                        print(f"DEBUG: Processing base64 image")
                        
                        # Split the data URL to get just the base64 part
                        format_part, imgstr = image_src.split(';base64,')
                        ext = format_part.split('/')[-1]  # Get file extension
                        
                        # Decode base64 to binary
                        img_data = base64.b64decode(imgstr)
                        print(f"DEBUG: Decoded image data, size: {len(img_data)} bytes")
                        
                        # Create file name
                        original_name = image_data.get('name', 'uploaded_image.jpg')
                        file_name = f"{self.object.slug}_{original_name}"
                        print(f"DEBUG: Creating file: {file_name}")
                        
                        # Create Django file object
                        img_file = ContentFile(img_data, name=file_name)
                        
                        # Create ProductImage instance
                        product_image = ProductImage(
                            product=self.object,
                            image=img_file,
                            alt_text=f"{self.object.name} image",
                            is_main=image_data.get('isMain', False)
                        )
                        product_image.save()
                        print(f"DEBUG: Successfully saved ProductImage {product_image.id}")
                        
                    else:
                        print(f"DEBUG: Image source doesn't start with data:image")
                        
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"ERROR: Processing image {field_name}: {e}")
                continue
        
        print(f"DEBUG: Finished processing images. Total images for product: {self.object.images.count()}")




class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'admin/products/form.html'
    success_url = reverse_lazy('products:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Product updated successfully!')
        return super().form_valid(form)


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
        return Category.objects.annotate(
            product_count=models.Count('products')
        ).order_by('name')


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


def is_admin_user(user):
    return user.is_staff or user.is_superuser

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