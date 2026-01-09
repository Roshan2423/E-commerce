from django.urls import path
from . import user_views

app_name = 'user_management'

urlpatterns = [
    # User management URLs for admin panel
    path('', user_views.UserListView.as_view(), name='user_list'),
    path('<int:pk>/', user_views.UserDetailView.as_view(), name='user_detail'),
    path('<int:pk>/edit/', user_views.edit_user, name='user_edit'),
    path('<int:user_id>/toggle-status/', user_views.toggle_user_status, name='toggle_user_status'),
    path('<int:user_id>/toggle-verification/', user_views.toggle_user_verification, name='toggle_user_verification'),
    path('<int:user_id>/toggle-admin/', user_views.toggle_admin_status, name='toggle_admin_status'),
    path('<int:user_id>/delete/', user_views.delete_user, name='delete_user'),
    path('bulk-actions/', user_views.bulk_user_actions, name='bulk_user_actions'),
]