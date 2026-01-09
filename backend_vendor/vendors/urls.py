"""
Vendor Dashboard URLs
/vendor/ - Vendor's own dashboard
"""
from django.urls import path
from . import views
from . import application_views

app_name = 'vendor'

urlpatterns = [
    # Vendor Application
    path('become-vendor/', application_views.BecomeVendorView.as_view(), name='become_vendor'),
    path('apply/', application_views.VendorApplicationCreateView.as_view(), name='apply'),
    path('apply/success/', application_views.VendorApplicationSuccessView.as_view(), name='application_success'),
    path('apply/status/<int:pk>/', application_views.VendorApplicationStatusView.as_view(), name='application_status'),
    path('apply/my-applications/', application_views.MyApplicationsView.as_view(), name='my_applications'),

    # Dashboard
    path('', views.VendorDashboardView.as_view(), name='dashboard'),

    # Profile
    path('profile/', views.VendorProfileView.as_view(), name='profile'),

    # Pages (About & Contact)
    path('pages/', views.VendorPagesView.as_view(), name='pages'),

    # Products
    path('products/', views.VendorProductListView.as_view(), name='products'),
    path('products/add/', views.VendorProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/', views.VendorProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/edit/', views.VendorProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.VendorProductDeleteView.as_view(), name='product_delete'),

    # Categories
    path('categories/', views.VendorCategoryListView.as_view(), name='categories'),
    path('categories/add/', views.VendorCategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.VendorCategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.vendor_category_delete, name='category_delete'),

    # Flash Sale Management
    path('flash-sale/', views.VendorFlashSaleView.as_view(), name='flash_sale'),
    path('flash-sale/toggle/<int:pk>/', views.vendor_toggle_flash_sale, name='toggle_flash_sale'),
    path('flash-sale/update-price/<int:pk>/', views.vendor_update_flash_price, name='update_flash_price'),

    # Orders
    path('orders/', views.VendorOrderListView.as_view(), name='orders'),
    path('orders/<uuid:order_id>/', views.VendorOrderDetailView.as_view(), name='order_detail'),

    # Reviews
    path('reviews/', views.VendorReviewListView.as_view(), name='reviews'),
    path('reviews/<int:pk>/respond/', views.vendor_review_respond, name='review_respond'),
    path('reviews/<int:pk>/<str:action>/', views.vendor_review_action, name='review_action'),

    # Customers
    path('customers/', views.VendorCustomerListView.as_view(), name='customers'),
    path('customers/<int:pk>/', views.VendorCustomerDetailView.as_view(), name='customer_detail'),

    # Messages
    path('messages/', views.VendorMessageListView.as_view(), name='messages'),
    path('messages/<int:pk>/', views.VendorMessageThreadView.as_view(), name='message_thread'),
    path('messages/reply/', views.vendor_message_reply, name='message_reply'),

    # Storefront Customization
    path('storefront/', views.StorefrontCustomizeView.as_view(), name='storefront'),
    path('storefront/preview/', views.storefront_preview, name='storefront_preview'),
    path('storefront/restore/', views.storefront_restore, name='storefront_restore'),

    # Analytics
    path('analytics/', views.VendorAnalyticsView.as_view(), name='analytics'),

    # Upgrade
    path('upgrade/', views.VendorUpgradeView.as_view(), name='upgrade'),
]
