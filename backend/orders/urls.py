from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.OrderListView.as_view(), name='list'),
    path('<uuid:order_id>/', views.OrderDetailView.as_view(), name='detail'),
    path('<uuid:order_id>/update/', views.OrderUpdateView.as_view(), name='update'),
    path('<uuid:order_id>/cancel/', views.OrderCancelView.as_view(), name='cancel'),
]