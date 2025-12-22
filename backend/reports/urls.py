from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsHomeView.as_view(), name='home'),
    path('sales/', views.SalesReportView.as_view(), name='sales'),
    path('products/', views.ProductReportView.as_view(), name='products'),
    path('customers/', views.CustomerReportView.as_view(), name='customers'),
]