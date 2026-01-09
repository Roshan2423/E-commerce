"""
Super Admin - Vendor Management URLs
/admin/vendors/ - Manage registered businesses
"""
from django.urls import path
from . import views

app_name = 'vendor_admin'

urlpatterns = [
    # List all businesses
    path('', views.AdminVendorListView.as_view(), name='list'),

    # Add new business
    path('add/', views.AdminVendorAddView.as_view(), name='add'),

    # Business detail
    path('<int:pk>/', views.AdminVendorDetailView.as_view(), name='detail'),

    # Edit business
    path('<int:pk>/edit/', views.AdminVendorEditView.as_view(), name='edit'),

    # Actions
    path('<int:pk>/approve/', views.vendor_approve, name='approve'),
    path('<int:pk>/suspend/', views.vendor_suspend, name='suspend'),
    path('<int:pk>/reject/', views.vendor_reject, name='reject'),
    path('<int:pk>/delete/', views.AdminVendorDeleteView.as_view(), name='delete'),

    # Stats API
    path('<int:pk>/stats/', views.vendor_stats_api, name='stats'),

    # Vendor Applications
    path('applications/', views.AdminApplicationListView.as_view(), name='applications'),
    path('applications/<int:pk>/', views.AdminApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<int:pk>/approve/', views.application_approve, name='application_approve'),
    path('applications/<int:pk>/reject/', views.application_reject, name='application_reject'),

    # Subscription Management
    path('<int:pk>/extend-trial/', views.admin_extend_trial, name='extend_trial'),
    path('<int:pk>/change-plan/', views.admin_change_plan, name='change_plan'),
    path('<int:pk>/activate-subscription/', views.admin_activate_subscription, name='activate_subscription'),
    path('<int:pk>/cancel-trial/', views.admin_cancel_trial, name='cancel_trial'),
]
