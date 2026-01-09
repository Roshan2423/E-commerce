"""
Multi-Vendor E-Commerce Models
Business registration, storefront customization, and vendor messaging
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta


# Trial duration constant
TRIAL_DURATION_DAYS = 14


class Business(models.Model):
    """
    Registered business that can become a vendor.
    Super admin adds email here, when user with that email logs in,
    they become the owner of this business.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    PLAN_CHOICES = [
        ('starter', 'Starter Pack'),
        ('professional', 'Professional Pack'),
    ]

    SUBSCRIPTION_STATUS_CHOICES = [
        ('trial', 'Trial Period'),
        ('active', 'Active Subscription'),
        ('expired', 'Trial Expired'),
        ('cancelled', 'Cancelled'),
    ]

    # Basic Info
    email = models.EmailField(unique=True, help_text="Business owner's email")
    business_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to='business_logos/',
        blank=True,
        null=True,
        help_text="Business logo (optional)"
    )

    # Owner (linked when user with this email logs in)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='business'
    )

    # Status and approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_businesses'
    )

    # Commission settings (for future use)
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text="Platform commission percentage"
    )

    # Subscription/Plan fields
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='starter',
        help_text="Current subscription plan"
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='trial',
        help_text="Current subscription status"
    )
    trial_start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the trial period started"
    )
    trial_end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the trial period ends"
    )
    subscription_start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When paid subscription started"
    )
    welcome_message_shown = models.BooleanField(
        default=False,
        help_text="Whether welcome message has been shown after approval"
    )
    trial_expiry_email_sent = models.BooleanField(
        default=False,
        help_text="Whether trial expiry reminder email has been sent"
    )

    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Business'
        verbose_name_plural = 'Businesses'
        ordering = ['-created_at']

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            base_slug = slugify(self.business_name)
            slug = base_slug
            counter = 1
            while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Set approved_at when status changes to approved
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == 'approved'

    @property
    def is_linked(self):
        return self.owner is not None

    def get_total_products(self):
        return self.products.filter(is_active=True).count()

    def get_total_orders(self):
        return self.order_items.values('order').distinct().count()

    def get_total_revenue(self):
        from django.db.models import Sum
        result = self.order_items.filter(
            order__payment_status='paid'
        ).aggregate(total=Sum('total_price'))
        return result['total'] or 0

    # Subscription helper methods
    @property
    def is_trial_active(self):
        """Check if trial period is still active"""
        if self.subscription_status != 'trial':
            return False
        if not self.trial_end_date:
            return False
        return timezone.now() < self.trial_end_date

    @property
    def trial_days_remaining(self):
        """Calculate remaining trial days"""
        if not self.trial_end_date:
            return 0
        remaining = self.trial_end_date - timezone.now()
        return max(0, remaining.days)

    @property
    def is_subscription_active(self):
        """Check if vendor has active access (trial or paid)"""
        if self.subscription_status == 'active':
            return True
        if self.subscription_status == 'trial':
            return self.is_trial_active
        return False

    def start_trial(self):
        """Start the trial period"""
        self.subscription_status = 'trial'
        self.trial_start_date = timezone.now()
        self.trial_end_date = timezone.now() + timedelta(days=TRIAL_DURATION_DAYS)
        self.save(update_fields=['subscription_status', 'trial_start_date', 'trial_end_date'])

    def expire_trial(self):
        """Mark trial as expired"""
        self.subscription_status = 'expired'
        self.save(update_fields=['subscription_status'])

    def activate_subscription(self):
        """Activate paid subscription"""
        self.subscription_status = 'active'
        self.subscription_start_date = timezone.now()
        self.save(update_fields=['subscription_status', 'subscription_start_date'])


class VendorStorefront(models.Model):
    """
    Storefront customization settings for each vendor.
    Allows vendors to customize their store appearance.
    """
    LAYOUT_CHOICES = [
        ('grid', 'Grid Layout'),
        ('list', 'List Layout'),
        ('masonry', 'Masonry Layout'),
    ]

    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name='storefront'
    )

    # Hero Section
    hero_image = models.ImageField(
        upload_to='vendors/hero/',
        blank=True,
        null=True,
        help_text="Hero banner image (recommended: 1920x600)"
    )
    hero_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Main headline on hero section"
    )
    hero_subtitle = models.CharField(
        max_length=500,
        blank=True,
        help_text="Subtitle or description"
    )
    hero_cta_text = models.CharField(
        max_length=50,
        default='Shop Now',
        help_text="Call to action button text"
    )
    hero_cta_link = models.CharField(
        max_length=200,
        blank=True,
        help_text="CTA button link (leave empty for products page)"
    )

    # Navbar/Branding
    logo = models.ImageField(
        upload_to='vendors/logos/',
        blank=True,
        null=True,
        help_text="Store logo (recommended: 200x50)"
    )
    favicon = models.ImageField(
        upload_to='vendors/favicons/',
        blank=True,
        null=True,
        help_text="Favicon for browser tab"
    )
    primary_color = models.CharField(
        max_length=7,
        default='#6366f1',
        help_text="Primary brand color (hex)"
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#8b5cf6',
        help_text="Secondary color (hex)"
    )
    accent_color = models.CharField(
        max_length=7,
        default='#06b6d4',
        help_text="Accent color for highlights (hex)"
    )

    # Layout preferences
    product_layout = models.CharField(
        max_length=20,
        choices=LAYOUT_CHOICES,
        default='grid'
    )
    products_per_page = models.PositiveIntegerField(default=12)
    show_flash_sale = models.BooleanField(
        default=True,
        help_text="Show flash sale section on storefront"
    )
    show_categories = models.BooleanField(
        default=True,
        help_text="Show category navigation"
    )

    # Professional Layout Builder fields
    layout_template = models.CharField(
        max_length=50,
        default='classic',
        help_text="Layout template style (classic, modern, minimal)"
    )
    section_order = models.TextField(
        blank=True,
        default='hero,categories,featured,new-arrivals,deals,testimonials,newsletter',
        help_text="Comma-separated order of storefront sections"
    )
    sections_enabled = models.TextField(
        blank=True,
        default='hero,categories,featured,new-arrivals,newsletter',
        help_text="Comma-separated list of enabled sections"
    )
    show_hero = models.BooleanField(
        default=True,
        help_text="Show hero banner section"
    )
    show_featured = models.BooleanField(
        default=True,
        help_text="Show featured products section"
    )
    show_new_arrivals = models.BooleanField(
        default=True,
        help_text="Show new arrivals section"
    )
    show_testimonials = models.BooleanField(
        default=False,
        help_text="Show testimonials section"
    )
    show_newsletter = models.BooleanField(
        default=True,
        help_text="Show newsletter subscription section"
    )

    # ============ PROFESSIONAL PLAN: ADVANCED CUSTOMIZATION ============

    # Header Style Options
    HEADER_STYLE_CHOICES = [
        ('classic', 'Classic - Centered Logo'),
        ('modern', 'Modern - Left Logo + Mega Menu'),
        ('minimal', 'Minimal - Hamburger Menu'),
    ]
    header_style = models.CharField(
        max_length=20,
        choices=HEADER_STYLE_CHOICES,
        default='classic',
        help_text="Header layout style (Professional plan)"
    )

    # Hero Banner Style Options
    HERO_STYLE_CHOICES = [
        ('full_width', 'Full-Width Image'),
        ('split', 'Split - Image + Text Side by Side'),
        ('slider', 'Slider/Carousel'),
    ]
    hero_style = models.CharField(
        max_length=20,
        choices=HERO_STYLE_CHOICES,
        default='full_width',
        help_text="Hero banner layout style (Professional plan)"
    )

    # Additional Hero Slides (for slider style - max 3 slides)
    hero_image_2 = models.ImageField(
        upload_to='vendors/hero/',
        blank=True,
        null=True,
        help_text="Second hero image for slider (1920x600)"
    )
    hero_image_3 = models.ImageField(
        upload_to='vendors/hero/',
        blank=True,
        null=True,
        help_text="Third hero image for slider (1920x600)"
    )
    hero_title_2 = models.CharField(max_length=200, blank=True)
    hero_subtitle_2 = models.CharField(max_length=500, blank=True)
    hero_cta_text_2 = models.CharField(max_length=50, blank=True, default='')
    hero_cta_link_2 = models.CharField(max_length=200, blank=True)
    hero_title_3 = models.CharField(max_length=200, blank=True)
    hero_subtitle_3 = models.CharField(max_length=500, blank=True)
    hero_cta_text_3 = models.CharField(max_length=50, blank=True, default='')
    hero_cta_link_3 = models.CharField(max_length=200, blank=True)

    # Hero Color Overlay (Professional plan)
    hero_overlay_color = models.CharField(
        max_length=7,
        default='#000000',
        help_text="Overlay color for hero banner (hex)"
    )
    hero_overlay_opacity = models.PositiveIntegerField(
        default=30,
        help_text="Overlay opacity percentage (0-100)"
    )

    # Storefront Template Selection (Professional plan)
    TEMPLATE_CHOICES = [
        ('classic', 'Classic Template'),
        ('modern', 'Modern Template'),
        ('minimal', 'Minimal Template'),
    ]
    storefront_template = models.CharField(
        max_length=20,
        choices=TEMPLATE_CHOICES,
        default='classic',
        help_text="Complete storefront template style"
    )

    # Dashboard Theme Colors (Professional plan)
    dashboard_primary_color = models.CharField(
        max_length=7,
        default='#6366f1',
        help_text="Dashboard primary color (hex)"
    )
    dashboard_sidebar_color = models.CharField(
        max_length=7,
        default='#111827',
        help_text="Dashboard sidebar background color (hex)"
    )
    dashboard_accent_color = models.CharField(
        max_length=7,
        default='#10b981',
        help_text="Dashboard accent color (hex)"
    )

    # ============ END PROFESSIONAL PLAN FIELDS ============

    # Social links
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # SEO
    meta_title = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO title (defaults to business name)"
    )
    meta_description = models.TextField(
        max_length=320,
        blank=True,
        help_text="SEO description"
    )

    # Analytics (optional)
    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Google Analytics tracking ID"
    )
    facebook_pixel_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Facebook Pixel ID"
    )

    # ============ ABOUT PAGE CONTENT ============
    about_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="About page headline (defaults to 'About [Store Name]')"
    )
    about_tagline = models.CharField(
        max_length=300,
        blank=True,
        help_text="Short tagline below the title"
    )
    about_story = models.TextField(
        blank=True,
        help_text="Your store's story - how you started, your journey"
    )
    about_mission = models.TextField(
        blank=True,
        help_text="Your mission statement - what drives your business"
    )
    about_vision = models.TextField(
        blank=True,
        help_text="Your vision - where you see your business going"
    )

    # ============ CONTACT PAGE CONTENT ============
    contact_address = models.CharField(
        max_length=300,
        blank=True,
        help_text="Full business address"
    )
    contact_city = models.CharField(
        max_length=100,
        blank=True,
        default='Nepal',
        help_text="City/Country"
    )
    contact_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Contact phone number"
    )
    contact_email = models.EmailField(
        blank=True,
        help_text="Contact email address"
    )
    contact_hours = models.CharField(
        max_length=200,
        blank=True,
        default='Sun - Fri: 10 AM - 6 PM',
        help_text="Business hours"
    )
    contact_hours_note = models.CharField(
        max_length=100,
        blank=True,
        default='Saturday: Closed',
        help_text="Additional note about hours"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Vendor Storefront'
        verbose_name_plural = 'Vendor Storefronts'

    def __str__(self):
        return f"Storefront: {self.business.business_name}"

    def get_hero_image_url(self):
        if self.hero_image:
            return self.hero_image.url
        return None

    def get_logo_url(self):
        if self.logo:
            return self.logo.url
        return None


class VendorMessage(models.Model):
    """
    Messages between customers and vendors.
    Supports threaded conversations.
    """
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_messages'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendor_messages',
        help_text="Related order (if applicable)"
    )

    subject = models.CharField(max_length=200)
    message = models.TextField()

    # Reply tracking
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    is_read = models.BooleanField(default=False)
    is_from_vendor = models.BooleanField(
        default=False,
        help_text="True if sent by vendor, False if sent by customer"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vendor Message'
        verbose_name_plural = 'Vendor Messages'

    def __str__(self):
        sender = "Vendor" if self.is_from_vendor else "Customer"
        return f"{sender}: {self.subject[:50]}"

    def get_thread(self):
        """Get all messages in this thread"""
        if self.parent:
            return self.parent.get_thread()
        return VendorMessage.objects.filter(
            models.Q(pk=self.pk) | models.Q(parent=self)
        ).order_by('created_at')

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


class VendorPayout(models.Model):
    """
    Track vendor payouts (for future commission system)
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_deducted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Period
    period_start = models.DateField()
    period_end = models.DateField()

    # Payment details
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payout #{self.pk} - {self.business.business_name} - Rs. {self.net_amount}"


class VendorApplication(models.Model):
    """
    Vendor application submitted by users who want to become vendors.
    Admin reviews and approves/rejects applications.
    On approval, a Business is created and linked to the user.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('more_info', 'More Info Needed'),
    ]

    CATEGORY_CHOICES = [
        ('electronics', 'Electronics & Gadgets'),
        ('fashion', 'Fashion & Apparel'),
        ('beauty', 'Beauty & Personal Care'),
        ('home', 'Home & Living'),
        ('food', 'Food & Beverages'),
        ('sports', 'Sports & Outdoors'),
        ('books', 'Books & Stationery'),
        ('toys', 'Toys & Games'),
        ('automotive', 'Automotive'),
        ('other', 'Other'),
    ]

    PLAN_CHOICES = [
        ('starter', 'Starter Pack'),
        ('professional', 'Professional Pack'),
    ]

    # Applicant (the logged-in user)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_applications'
    )

    # Personal Details
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Your date of birth (mm/dd/yyyy)"
    )

    # Business Details
    business_name = models.CharField(max_length=200)
    business_email = models.EmailField()
    phone = models.CharField(max_length=20, help_text="Phone number with country code (e.g., +977-XXXXXXXXXX)")
    description = models.TextField(help_text="Describe your business and what you plan to sell")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    address = models.TextField()

    # Business Logo
    logo = models.ImageField(
        upload_to='vendor_applications/logos/',
        blank=True,
        null=True,
        help_text="Your company logo (optional - you can also just use your business name)"
    )

    # Optional documents
    business_document = models.FileField(
        upload_to='vendor_applications/',
        blank=True,
        null=True,
        help_text="Business registration or tax document (optional)"
    )

    # Plan selection
    selected_plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='starter',
        help_text="Subscription plan selected by the applicant"
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")
    rejection_reason = models.TextField(blank=True, help_text="Reason shown to user if rejected")

    # Review info
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Created business (set when approved)
    created_business = models.OneToOneField(
        Business,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='application'
    )

    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Vendor Application'
        verbose_name_plural = 'Vendor Applications'

    def __str__(self):
        return f"Application: {self.business_name} ({self.get_status_display()})"

    def approve(self, admin_user):
        """Approve the application and create a Business with trial period"""
        if self.status == 'approved':
            return self.created_business

        # Set trial dates
        trial_start = timezone.now()
        trial_end = trial_start + timedelta(days=TRIAL_DURATION_DAYS)

        # Create the business with plan and trial info
        business = Business.objects.create(
            email=self.business_email,
            business_name=self.business_name,
            description=self.description,
            logo=self.logo if self.logo else None,
            phone=self.phone,
            address=self.address,
            owner=self.user,
            status='approved',
            approved_by=admin_user,
            approved_at=timezone.now(),
            # Subscription fields
            plan=self.selected_plan,
            subscription_status='trial',
            trial_start_date=trial_start,
            trial_end_date=trial_end,
        )

        # Update application
        self.status = 'approved'
        self.created_business = business
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()

        # Send approval email
        try:
            from .emails import send_vendor_approval_email
            send_vendor_approval_email(self, business)
        except Exception as e:
            # Log error but don't fail the approval
            print(f"Failed to send approval email: {e}")

        return business

    def reject(self, admin_user, reason=''):
        """Reject the application"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()

    def request_more_info(self, admin_user, notes=''):
        """Request more information from applicant"""
        self.status = 'more_info'
        self.admin_notes = notes
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
