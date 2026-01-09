from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    # API endpoint for frontend form submission
    path('api/contact/', views.submit_contact, name='submit_contact'),

    # Admin views
    path('admin/contacts/', views.contact_list, name='contact_list'),
    path('admin/contacts/<int:pk>/', views.contact_detail, name='contact_detail'),
    path('admin/contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
]
