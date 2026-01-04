"""
Chatbot Admin URLs
"""
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Admin views
    path('sessions/', views.chat_sessions_list, name='sessions'),
    path('sessions/<str:session_id>/', views.chat_session_detail, name='session_detail'),
    path('analytics/', views.chat_analytics_dashboard, name='analytics'),

    # API endpoints
    path('api/sessions/', views.api_sessions, name='api_sessions'),
    path('api/sessions/<str:session_id>/', views.api_session_detail, name='api_session_detail'),
    path('api/analytics/summary/', views.api_analytics_summary, name='api_analytics_summary'),
    path('api/analytics/daily/', views.api_daily_stats, name='api_daily_stats'),
    path('api/analytics/intents/', views.api_top_intents, name='api_top_intents'),
    path('api/analytics/hours/', views.api_peak_hours, name='api_peak_hours'),
]
