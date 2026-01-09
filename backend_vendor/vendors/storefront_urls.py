"""
Public Storefront URLs
/v/<vendor_slug>/ - Public vendor storefront (SPA)
"""
from django.urls import path, re_path
from . import api_views

app_name = 'storefront'

urlpatterns = [
    # APIs for storefront (must come before catch-all)
    path('api/config/', api_views.storefront_config_api, name='api_config'),
    path('api/products/', api_views.storefront_products_api, name='api_products'),
    path('api/product/<int:product_id>/', api_views.storefront_product_detail_api, name='api_product_detail'),
    path('api/flash-sale/', api_views.storefront_flash_sale_api, name='api_flash_sale'),
    path('api/categories/', api_views.storefront_categories_api, name='api_categories'),
    path('api/featured/', api_views.storefront_featured_api, name='api_featured'),
    path('api/new-arrivals/', api_views.storefront_new_arrivals_api, name='api_new_arrivals'),
    path('api/product/<int:product_id>/reviews/', api_views.storefront_product_reviews_api, name='api_product_reviews'),
    path('api/product/<int:product_id>/related/', api_views.storefront_related_products_api, name='api_related_products'),
    path('api/product/<int:product_id>/can-review/', api_views.storefront_can_review_api, name='api_can_review'),

    # Public storefront SPA - home page
    path('', api_views.storefront_home, name='home'),

    # Catch-all for SPA routes (product detail, flash-sale, cart, etc.)
    re_path(r'^(?P<spa_path>product|products|flash-sale|cart|checkout|categories|category|about|contact).*$',
            api_views.storefront_home, name='spa_catch_all'),
]
