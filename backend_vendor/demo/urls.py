from django.urls import path
from . import views, admin_views, api_views

app_name = 'demo'

urlpatterns = [
    # ============== Demo Settings (Admin) ==============
    path('settings/', admin_views.demo_settings_view, name='demo_settings'),

    # ============== Demo API Endpoints ==============
    # These mirror the product APIs but return admin-selected demo products
    path('api/products/', api_views.demo_products_api, name='api_products'),
    path('api/products/flash-sale/', api_views.demo_flash_sale_api, name='api_flash_sale'),
    path('api/products/featured/', api_views.demo_featured_api, name='api_featured'),
    path('api/products/new-arrivals/', api_views.demo_new_arrivals_api, name='api_new_arrivals'),
    path('api/products/<int:product_id>/', api_views.demo_product_detail_api, name='api_product_detail'),
    path('api/categories/', api_views.demo_categories_api, name='api_categories'),
    path('api/site-stats/', api_views.demo_site_stats_api, name='api_site_stats'),

    # ============== Starter Demo ==============
    # User Demo (Storefront)
    path('user/', views.user_home, name='user_home'),
    path('user/product/<int:product_id>/', views.user_product, name='user_product'),
    path('user/cart/', views.user_cart, name='user_cart'),

    # Admin Demo
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/products/add/', views.admin_add_product, name='admin_add_product'),
    path('admin/orders/', views.admin_orders, name='admin_orders'),

    # ============== Professional Demo ==============
    # Professional User Demo
    path('pro/user/', views.pro_user_home, name='pro_user_home'),
    path('pro/user/product/<int:product_id>/', views.pro_user_product, name='pro_user_product'),
    path('pro/user/cart/', views.pro_user_cart, name='pro_user_cart'),
    path('pro/user/checkout/', views.pro_user_checkout, name='pro_user_checkout'),
    # Catch-all for SPA routes within pro user demo
    path('pro/user/<path:spa_path>', views.pro_user_home, name='pro_user_spa'),

    # Professional Admin Demo
    path('pro/admin/', views.pro_admin_dashboard, name='pro_admin_dashboard'),
    path('pro/admin/products/', views.pro_admin_products, name='pro_admin_products'),
    path('pro/admin/orders/', views.pro_admin_orders, name='pro_admin_orders'),
    path('pro/admin/reviews/', views.pro_admin_reviews, name='pro_admin_reviews'),
    path('pro/admin/customers/', views.pro_admin_customers, name='pro_admin_customers'),
    path('pro/admin/analytics/', views.pro_admin_analytics, name='pro_admin_analytics'),
    path('pro/admin/messages/', views.pro_admin_messages, name='pro_admin_messages'),
    path('pro/admin/storefront/', views.pro_admin_storefront, name='pro_admin_storefront'),
]
