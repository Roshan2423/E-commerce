"""
Flask API Server for OVN Store Advanced Chatbot
Features: Rate limiting, Admin endpoints, Session persistence
Run this to start the chatbot web service
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from functools import wraps
import os
import atexit

from chatbot import OVNStoreChatbot
from core.security import security_middleware, sanitize_input, check_rate_limit
from core.error_messages import get_friendly_error, build_error_response
from core.persistence import get_session_store, get_analytics_store

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for frontend access

# Initialize single chatbot instance (handles sessions internally)
chatbot = OVNStoreChatbot()

# Admin authentication (simple token-based for demo)
ADMIN_TOKEN = os.getenv('CHATBOT_ADMIN_TOKEN', 'admin-secret-token')


def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Admin-Token') or request.args.get('token')
        if token != ADMIN_TOKEN:
            return jsonify({'error': 'Unauthorized', 'success': False}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    """Serve the chat interface"""
    return send_from_directory('.', 'index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with rate limiting and input sanitization"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        phone = data.get('phone')  # Optional: for returning customer detection

        # Rate limit check
        allowed, wait_seconds = check_rate_limit(session_id)
        if not allowed:
            return jsonify(build_error_response(
                'rate_limited',
                include_quick_replies=False
            )), 429

        # Sanitize input
        user_message = sanitize_input(user_message)

        if not user_message:
            return jsonify(build_error_response('empty_message')), 400

        # Get response from chatbot
        result = chatbot.chat(user_message, session_id)

        # Save session to MongoDB after each message
        try:
            chatbot.session_manager.save_session(session_id)
        except Exception as e:
            print(f"Warning: Could not save session: {e}")

        return jsonify({
            'success': True,
            'response': result.get('response', result.get('message', '')),
            'products': result.get('products', []),
            'categories': result.get('categories', []),
            'quick_replies': result.get('quick_replies', []),
            'intent': result.get('intent', 'general'),
            'metadata': result.get('metadata', {}),
            'session_id': session_id
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': get_friendly_error('server_error'),
            'error_detail': str(e) if app.debug else None
        }), 500


@app.route('/api/clear', methods=['POST'])
def clear_session():
    """Clear session and conversation history"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')

        chatbot.clear_session(session_id)

        return jsonify({
            'success': True,
            'message': 'Session cleared'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/session', methods=['GET'])
def get_session():
    """Get session info for debugging"""
    try:
        session_id = request.args.get('session_id', 'default')
        session_info = chatbot.get_session_info(session_id)

        return jsonify({
            'success': True,
            'session': session_info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/session/history', methods=['GET'])
def get_session_history():
    """Get previous sessions for a phone number"""
    try:
        phone = request.args.get('phone', '')
        if not phone or len(phone) != 10:
            return jsonify({
                'success': False,
                'error': 'Valid 10-digit phone required'
            }), 400

        sessions = chatbot.session_manager.get_sessions_by_phone(phone, limit=5)

        return jsonify({
            'success': True,
            'sessions': sessions
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        active_sessions = chatbot.get_active_sessions()
        return jsonify({
            'status': 'healthy',
            'active_sessions': active_sessions
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# ============================================
# Admin Endpoints
# ============================================

@app.route('/api/admin/sessions', methods=['GET'])
@require_admin
def admin_get_sessions():
    """Get all active chat sessions for admin panel"""
    try:
        session_store = get_session_store()

        # Get filters from query params
        filters = {}
        if request.args.get('phone'):
            filters['phone'] = request.args.get('phone')
        if request.args.get('admin_handling'):
            filters['admin_handling'] = request.args.get('admin_handling') == 'true'

        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        # Get from MongoDB
        sessions = session_store.get_all_sessions(filters, limit, offset)
        total = session_store.count_sessions(filters)

        # Also get in-memory active sessions
        active_in_memory = len(chatbot.session_manager.get_all_active_sessions())

        return jsonify({
            'success': True,
            'sessions': sessions,
            'total': total,
            'active_in_memory': active_in_memory,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/session/<session_id>', methods=['GET'])
@require_admin
def admin_get_session_detail(session_id):
    """Get detailed session info including conversation history"""
    try:
        session_store = get_session_store()
        session = session_store.load_session(session_id)

        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        return jsonify({
            'success': True,
            'session': session
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/takeover/<session_id>', methods=['POST'])
@require_admin
def admin_takeover_session(session_id):
    """Take over a chat session (admin starts handling)"""
    try:
        data = request.json or {}
        admin_id = data.get('admin_id', 1)

        success = chatbot.session_manager.set_admin_handling(session_id, admin_id, True)

        if success:
            # Add system message to session
            session = chatbot.session_manager.get(session_id)
            if session:
                session.add_message('system', 'An admin has joined this conversation.')
                session.save_to_db()

            return jsonify({
                'success': True,
                'message': 'Admin takeover successful'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found or takeover failed'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/release/<session_id>', methods=['POST'])
@require_admin
def admin_release_session(session_id):
    """Release a chat session back to bot"""
    try:
        data = request.json or {}
        admin_id = data.get('admin_id', 1)

        success = chatbot.session_manager.set_admin_handling(session_id, admin_id, False)

        if success:
            # Add system message
            session = chatbot.session_manager.get(session_id)
            if session:
                session.add_message('system', 'Admin has left the conversation. Bot is now assisting you.')
                session.save_to_db()

            return jsonify({
                'success': True,
                'message': 'Session released to bot'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/message', methods=['POST'])
@require_admin
def admin_send_message():
    """Send a message as admin to a session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        message = data.get('message', '')
        admin_id = data.get('admin_id', 1)

        if not session_id or not message:
            return jsonify({
                'success': False,
                'error': 'session_id and message are required'
            }), 400

        # Get session
        session = chatbot.session_manager.get(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        # Ensure admin is handling this session
        if not getattr(session, 'admin_handling', False):
            return jsonify({
                'success': False,
                'error': 'Admin must takeover session first'
            }), 400

        # Add admin message
        session.add_message('admin', message)
        session.save_to_db()

        return jsonify({
            'success': True,
            'message': 'Message sent'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/analytics', methods=['GET'])
@require_admin
def admin_get_analytics():
    """Get chat analytics summary"""
    try:
        analytics_store = get_analytics_store()

        # Get date range
        days = int(request.args.get('days', 7))

        # Get various analytics
        daily_summary = analytics_store.get_daily_summary()
        top_intents = analytics_store.get_top_intents(days=days)
        peak_hours = analytics_store.get_peak_hours(days=days)
        conversion_stats = analytics_store.get_conversion_stats(days=days)

        return jsonify({
            'success': True,
            'today': daily_summary,
            'top_intents': top_intents,
            'peak_hours': peak_hours,
            'conversion': conversion_stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/active', methods=['GET'])
@require_admin
def admin_get_active_sessions():
    """Get currently active sessions (in-memory)"""
    try:
        sessions = chatbot.session_manager.get_all_active_sessions()

        session_data = []
        for session in sessions:
            session_data.append({
                'session_id': session.session_id,
                'user_phone': session.user_phone,
                'user_name': session.user_name,
                'state': session.state.value,
                'admin_handling': getattr(session, 'admin_handling', False),
                'last_activity': session.last_activity.isoformat(),
                'message_count': len(session.conversation_history)
            })

        return jsonify({
            'success': True,
            'sessions': session_data,
            'count': len(session_data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# Shutdown Handler
# ============================================

def save_sessions_on_shutdown():
    """Save all sessions to MongoDB before shutdown"""
    print("Saving sessions before shutdown...")
    saved = chatbot.session_manager.save_all_sessions()
    print(f"Saved {saved} sessions to MongoDB")


# Register shutdown handler
atexit.register(save_sessions_on_shutdown)


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("OVN STORE ADVANCED CHATBOT SERVER")
    print("=" * 50)
    print("Starting server at http://localhost:5000")
    print("Open your browser and go to http://localhost:5000")
    print("\nAdmin API available at /api/admin/*")
    print(f"Admin token: {ADMIN_TOKEN[:4]}...{ADMIN_TOKEN[-4:]}")
    print("=" * 50 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
