from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='home'),
    path('api/groq-usage/', views.groq_usage_api, name='groq_usage'),
]