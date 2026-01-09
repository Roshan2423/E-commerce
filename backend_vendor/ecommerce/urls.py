"""
URL configuration for ecommerce project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import api_views, google_auth, views as account_views
from landing import views as landing_views

urlpatterns = [
    # Landing page (SaaS homepage)
    path('', landing_views.landing_page, name='home'),

    # Django admin (disabled - using custom admin)
    path('django-admin/', admin.site.urls),

    # API endpoints (direct paths, no nesting)
    path('api/login/', api_views.api_login, name='api_login'),
    path('api/logout/', api_views.api_logout, name='api_logout'),
    path('api/auth-status/', api_views.api_auth_status, name='api_auth_status'),
    path('api/csrf-token/', api_views.get_csrf_token, name='api_csrf_token'),
    path('api/google-auth/', google_auth.google_auth, name='google_auth'),
    path('api/products/', include('products.urls', namespace='products_api')),

    # Web auth routes
    path('login/', account_views.CustomLoginView.as_view(), name='login'),
    path('logout/', account_views.custom_logout_view, name='logout'),
    path('register/', account_views.RegisterView.as_view(), name='register'),

    # Admin panel routes
    path('dashboard/', include('dashboard.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('users/', include('accounts.user_urls')),
    path('reports/', include('reports.urls')),
    path('admin/chatbot/', include('chatbot.urls')),
    path('contact/', include('contacts.urls')),

    # Customer Dashboard
    path('account/', include('accounts.dashboard_urls', namespace='customer_dashboard')),
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Multi-Vendor Routes
    path('admin/vendors/', include('vendors.admin_urls')),  # Super admin vendor management
    path('vendor/', include('vendors.urls', namespace='vendor')),  # Vendor dashboard
    path('v/<slug:vendor_slug>/', include('vendors.storefront_urls')),  # Public vendor storefronts

    # E-commerce store (Demo Store)
    path('store/', include('frontend.urls', namespace='store')),

    # Demo pages for showcasing platform
    path('demo/', include('demo.urls', namespace='demo')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
