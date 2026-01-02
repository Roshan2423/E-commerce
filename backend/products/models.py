from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from PIL import Image
import os
import random
import string

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    STOCK_STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('low_stock', 'Low Stock'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.TextField(max_length=500, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    stock_status = models.CharField(max_length=15, choices=STOCK_STATUS_CHOICES, default='in_stock')
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    length = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Length in cm")
    width = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Width in cm")
    height = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Height in cm")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_flash_sale = models.BooleanField(default=False, help_text="Show this product in Flash Sale section")
    flash_sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Special price for flash sale")
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.TextField(max_length=320, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
            
        # Auto-generate SKU if not provided
        if not self.sku:
            self.sku = self.generate_unique_sku()
        
        # Update stock status based on quantity
        if self.stock_quantity <= 0:
            self.stock_status = 'out_of_stock'
        elif self.stock_quantity <= self.low_stock_threshold:
            self.stock_status = 'low_stock'
        else:
            self.stock_status = 'in_stock'
            
        super().save(*args, **kwargs)
    
    def generate_unique_slug(self):
        """Generate a unique slug for the product"""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        # Check if slug already exists (exclude current object if updating)
        while True:
            if self.pk:
                # Updating existing product - exclude self from duplicate check
                exists = Product.objects.filter(slug=slug).exclude(pk=self.pk).exists()
            else:
                # Creating new product
                exists = Product.objects.filter(slug=slug).exists()
            
            if not exists:
                return slug
            
            # If slug exists, append counter
            slug = f"{base_slug}-{counter}"
            counter += 1
    
    def generate_unique_sku(self):
        """Generate a unique SKU for the product"""
        # Create base SKU from product name (first 3 letters + category initials)
        name_part = ''.join([c.upper() for c in self.name if c.isalpha()])[:3]
        if len(name_part) < 3:
            name_part = name_part.ljust(3, 'X')
            
        category_part = ''.join([c.upper() for c in self.category.name.split() if c])[:2] if self.category else 'XX'
        if len(category_part) < 2:
            category_part = category_part.ljust(2, 'X')
            
        # Add random numbers for uniqueness
        while True:
            random_part = ''.join(random.choices(string.digits, k=4))
            sku = f"{name_part}{category_part}{random_part}"
            
            # Check if SKU already exists
            if not Product.objects.filter(sku=sku).exists():
                return sku

    def __str__(self):
        return self.name

    def get_discount_percentage(self):
        try:
            if self.compare_price and float(self.compare_price) > float(self.price):
                return round(((float(self.compare_price) - float(self.price)) / float(self.compare_price)) * 100, 0)
        except (TypeError, ValueError, AttributeError):
            pass
        return 0

    def get_main_image(self):
        try:
            # Use a simple approach to avoid complex filtering that breaks with Djongo
            images = list(self.images.all())
            for image in images:
                if hasattr(image, 'is_main') and image.is_main:
                    return image.image.url if image.image else None
            # If no main image, return the first image
            if images:
                return images[0].image.url if images[0].image else None
        except Exception:
            pass
        return None


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main', 'id']

    def save(self, *args, **kwargs):
        # If this is set as main image, remove main status from others
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)  # e.g., "Size", "Color"
    value = models.CharField(max_length=100)  # e.g., "Large", "Red"
    price_adjustment = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'name', 'value']

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"


class Review(models.Model):
    """Product reviews from customers who purchased the product"""

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # 1-5 stars
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, null=True, help_text="Admin reply to the review")
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user', 'order']  # One review per order per product

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"

    def save(self, *args, **kwargs):
        # Check if this is a verified purchase
        if self.order and self.order.status == 'delivered':
            self.is_verified_purchase = True
        super().save(*args, **kwargs)


class ReviewImage(models.Model):
    """Images uploaded with reviews"""

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='reviews/')
    alt_text = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Image for review {self.review.id}"