from django.urls import path
from . import views, api_views

app_name = 'products'

urlpatterns = [
    # Admin views
    path('', views.product_list_view, name='list'),
    path('add/', views.ProductCreateView.as_view(), name='add'),
    path('<int:pk>/', views.product_detail_view, name='detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='delete'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.delete_category, name='category_delete'),

    # Flash Sale
    path('flash-sale/', views.flash_sale_view, name='flash_sale'),
    path('flash-sale/toggle/<int:pk>/', views.toggle_flash_sale, name='toggle_flash_sale'),
    path('flash-sale/update-price/<int:pk>/', views.update_flash_price, name='update_flash_price'),

    # Review admin views
    path('reviews/', views.review_list_view, name='reviews'),
    path('reviews/<int:pk>/', views.review_detail_view, name='review_detail'),
    path('reviews/<int:pk>/edit/', views.review_update_view, name='review_edit'),
    path('reviews/<int:pk>/delete/', views.review_delete_view, name='review_delete'),
    path('reviews/<int:pk>/<str:action>/', views.review_quick_action, name='review_action'),

    # API endpoints for frontend
    path('api/list/', api_views.products_api, name='api_list'),
    path('api/flash-sale/', api_views.flash_sale_api, name='api_flash_sale'),
    path('api/categories/', api_views.categories_api, name='api_categories'),
    path('api/<int:product_id>/', api_views.product_detail_api, name='api_detail'),

    # Review API endpoints
    path('api/<int:product_id>/reviews/', api_views.product_reviews_api, name='api_reviews'),
    path('api/<int:product_id>/can-review/', api_views.can_review_product, name='api_can_review'),
    path('api/<int:product_id>/submit-review/', api_views.submit_review, name='api_submit_review'),
    path('api/my-reviews/', api_views.my_reviews_api, name='api_my_reviews'),

    # Site stats API
    path('api/site-stats/', api_views.site_stats_api, name='api_site_stats'),
]