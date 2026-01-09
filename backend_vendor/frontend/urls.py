from django.urls import path, re_path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.index, name='index'),
    # Catch-all for SPA routes (cart, products, product detail, checkout, flash-sale, etc.)
    re_path(r'^(?P<path>login|register|cart|checkout|profile|products|product|categories|category|order-confirmation|my-orders|my-reviews|about|contact|flash-sale).*$', views.catch_all, name='catch_all'),
]
