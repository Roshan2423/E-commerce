"""
Customer Dashboard URL Configuration
"""
from django.urls import path
from . import dashboard_views

app_name = 'customer_dashboard'

urlpatterns = [
    # Dashboard Overview
    path('', dashboard_views.DashboardOverviewView.as_view(), name='overview'),

    # Orders
    path('orders/', dashboard_views.OrderListView.as_view(), name='orders'),
    path('orders/<uuid:order_id>/', dashboard_views.OrderDetailView.as_view(), name='order_detail'),

    # Addresses
    path('addresses/', dashboard_views.AddressListView.as_view(), name='addresses'),
    path('addresses/add/', dashboard_views.AddressCreateView.as_view(), name='address_add'),
    path('addresses/<int:pk>/edit/', dashboard_views.AddressUpdateView.as_view(), name='address_edit'),
    path('addresses/<int:pk>/delete/', dashboard_views.AddressDeleteView.as_view(), name='address_delete'),

    # Reviews
    path('reviews/', dashboard_views.ReviewListView.as_view(), name='reviews'),

    # Settings
    path('profile/', dashboard_views.ProfileUpdateView.as_view(), name='profile'),
    path('settings/', dashboard_views.SettingsView.as_view(), name='settings'),

    # API
    path('api/stats/', dashboard_views.api_dashboard_stats, name='api_stats'),
]
