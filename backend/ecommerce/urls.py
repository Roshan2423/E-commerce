"""
URL configuration for ecommerce project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import api_views, google_auth, views as account_views

urlpatterns = [
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
    path('logout/', account_views.custom_logout_view, name='logout'),

    # Admin panel routes
    path('dashboard/', include('dashboard.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('users/', include('accounts.user_urls')),
    path('reports/', include('reports.urls')),
    path('', include('contacts.urls')),

    # Frontend routes (must be last - catches all remaining URLs)
    path('', include('frontend.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
