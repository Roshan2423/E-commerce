"""
Chatbot Admin Views
Views for chat logs, session management, and analytics dashboard
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from .analytics import get_chat_analytics


@login_required
@staff_member_required
def chat_sessions_list(request):
    """View all chat sessions with filters"""
    analytics = get_chat_analytics()

    # Get filter parameters
    phone_filter = request.GET.get('phone', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    page = request.GET.get('page', 1)

    # Build filter query
    filters = {}
    if phone_filter:
        filters['user_phone'] = {'$regex': phone_filter, '$options': 'i'}
    if status_filter == 'active':
        filters['is_active'] = True
    elif status_filter == 'inactive':
        filters['is_active'] = False
    elif status_filter == 'admin':
        filters['admin_handling'] = True

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d')
            filters['created_at'] = {
                '$gte': filter_date,
                '$lt': filter_date + timedelta(days=1)
            }
        except ValueError:
            pass

    # Get sessions
    per_page = 20
    offset = (int(page) - 1) * per_page
    sessions = analytics.get_session_list(filters, limit=per_page, offset=offset)
    total_count = analytics.get_session_count(filters)

    # Calculate pagination
    total_pages = (total_count + per_page - 1) // per_page

    # Get summary stats
    summary = analytics.get_sessions_summary(days=7)

    context = {
        'sessions': sessions,
        'summary': summary,
        'phone_filter': phone_filter,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'page': int(page),
        'total_pages': total_pages,
        'total_count': total_count,
        'page_range': range(max(1, int(page) - 2), min(total_pages + 1, int(page) + 3))
    }

    return render(request, 'admin/chatbot/sessions.html', context)


@login_required
@staff_member_required
def chat_session_detail(request, session_id):
    """View detailed chat session with conversation history"""
    analytics = get_chat_analytics()

    session = analytics.get_session_detail(session_id)

    if not session:
        return render(request, 'admin/chatbot/detail.html', {
            'error': 'Session not found',
            'session_id': session_id
        })

    # Format conversation history
    conversation = session.get('conversation_history', [])

    context = {
        'session': session,
        'session_id': session_id,
        'conversation': conversation,
        'user_name': session.get('user_name') or session.get('user_info', {}).get('name', 'Anonymous'),
        'user_phone': session.get('user_phone') or session.get('user_info', {}).get('phone', ''),
        'state': session.get('state', 'idle'),
        'is_active': session.get('is_active', False),
        'admin_handling': session.get('admin_handling', False),
        'created_at': session.get('created_at'),
        'last_activity': session.get('last_activity')
    }

    return render(request, 'admin/chatbot/detail.html', context)


@login_required
@staff_member_required
def chat_analytics_dashboard(request):
    """Chat analytics dashboard with charts"""
    analytics = get_chat_analytics()

    days = int(request.GET.get('days', 7))

    # Get various analytics
    summary = analytics.get_sessions_summary(days=days)
    daily_stats = analytics.get_daily_stats(days=days)
    top_intents = analytics.get_top_intents(days=days, limit=10)
    peak_hours = analytics.get_peak_hours(days=days)
    conversion = analytics.get_conversion_stats(days=days)
    recent_messages = analytics.get_recent_messages(limit=20)

    context = {
        'summary': summary,
        'daily_stats': json.dumps(daily_stats),
        'top_intents': json.dumps(top_intents),
        'peak_hours': json.dumps(peak_hours),
        'conversion': conversion,
        'recent_messages': recent_messages,
        'days': days
    }

    return render(request, 'admin/chatbot/analytics.html', context)


# API Endpoints for AJAX calls

@login_required
@staff_member_required
@require_http_methods(['GET'])
def api_sessions(request):
    """API: Get sessions list"""
    analytics = get_chat_analytics()

    filters = {}
    if request.GET.get('phone'):
        filters['user_phone'] = {'$regex': request.GET.get('phone'), '$options': 'i'}
    if request.GET.get('active') == 'true':
        filters['is_active'] = True
    if request.GET.get('admin') == 'true':
        filters['admin_handling'] = True

    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))

    sessions = analytics.get_session_list(filters, limit=limit, offset=offset)
    total = analytics.get_session_count(filters)

    return JsonResponse({
        'success': True,
        'sessions': sessions,
        'total': total
    })


@login_required
@staff_member_required
@require_http_methods(['GET'])
def api_session_detail(request, session_id):
    """API: Get session detail"""
    analytics = get_chat_analytics()

    session = analytics.get_session_detail(session_id)

    if not session:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)

    return JsonResponse({
        'success': True,
        'session': session
    })


@login_required
@staff_member_required
@require_http_methods(['GET'])
def api_analytics_summary(request):
    """API: Get analytics summary"""
    analytics = get_chat_analytics()

    days = int(request.GET.get('days', 7))

    summary = analytics.get_sessions_summary(days=days)
    conversion = analytics.get_conversion_stats(days=days)

    return JsonResponse({
        'success': True,
        'summary': summary,
        'conversion': conversion
    })


@login_required
@staff_member_required
@require_http_methods(['GET'])
def api_daily_stats(request):
    """API: Get daily statistics"""
    analytics = get_chat_analytics()

    days = int(request.GET.get('days', 7))
    daily_stats = analytics.get_daily_stats(days=days)

    return JsonResponse({
        'success': True,
        'stats': daily_stats
    })


@login_required
@staff_member_required
@require_http_methods(['GET'])
def api_top_intents(request):
    """API: Get top intents"""
    analytics = get_chat_analytics()

    days = int(request.GET.get('days', 7))
    limit = int(request.GET.get('limit', 10))
    top_intents = analytics.get_top_intents(days=days, limit=limit)

    return JsonResponse({
        'success': True,
        'intents': top_intents
    })


@login_required
@staff_member_required
@require_http_methods(['GET'])
def api_peak_hours(request):
    """API: Get peak hours"""
    analytics = get_chat_analytics()

    days = int(request.GET.get('days', 7))
    peak_hours = analytics.get_peak_hours(days=days)

    return JsonResponse({
        'success': True,
        'hours': peak_hours
    })
