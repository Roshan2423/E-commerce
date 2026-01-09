from django.urls import path
from . import views
from . import api_views

app_name = 'orders'

urlpatterns = [
    # API endpoints for frontend
    path('api/create/', api_views.create_frontend_order, name='api_create'),
    path('api/check-login/', api_views.check_login_status, name='api_check_login'),
    path('api/my-orders/', api_views.get_user_orders, name='api_user_orders'),
    path('api/<uuid:order_id>/', api_views.get_order_detail, name='api_order_detail'),

    # Admin views
    path('', views.OrderListView.as_view(), name='list'),
    path('create/', views.create_order, name='create'),
    path('quick-update/', views.quick_update_order, name='quick_update'),
    path('deleted/', views.DeletedOrderListView.as_view(), name='deleted'),
    path('<uuid:order_id>/', views.OrderDetailView.as_view(), name='detail'),
    path('<uuid:order_id>/update/', views.update_order, name='update'),
    path('<uuid:order_id>/cancel/', views.OrderCancelView.as_view(), name='cancel'),
    path('<uuid:order_id>/delete/', views.soft_delete_order, name='soft_delete'),
    path('<uuid:order_id>/restore/', views.restore_order, name='restore'),
    path('<uuid:order_id>/permanent-delete/', views.permanent_delete_order, name='permanent_delete'),
]