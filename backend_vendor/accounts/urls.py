from django.urls import path
from . import views, api_views, google_auth

app_name = 'accounts'

urlpatterns = [
    # Web views
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),

    # Google OAuth (server-side flow - more reliable)
    path('google/', views.google_oauth_redirect, name='google_oauth_redirect'),
    path('google/callback/', views.google_oauth_callback, name='google_oauth_callback'),

    # API endpoints (note: these are included under /api/ prefix in main urls.py)
    path('login/', api_views.api_login, name='api_login'),
    path('logout/', api_views.api_logout, name='api_logout'),
    path('auth-status/', api_views.api_auth_status, name='api_auth_status'),
    path('csrf-token/', api_views.get_csrf_token, name='api_csrf_token'),
    path('google-auth/', google_auth.google_auth, name='google_auth'),
]