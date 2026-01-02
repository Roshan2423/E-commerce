"""
Flask API Server for OVN Store Chatbot
Run this to start the chatbot web service
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from chatbot import OVNStoreChatbot
import os

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for frontend access

# Initialize chatbot instance
chatbot = OVNStoreChatbot()

# Store session conversations (in production, use Redis or database)
sessions = {}

@app.route('/')
def index():
    """Serve the chat interface"""
    return send_from_directory('.', 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages - returns AI response + products with images"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        user_info = data.get('user_info', None)

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Get or create session
        if session_id not in sessions:
            sessions[session_id] = OVNStoreChatbot()

        bot = sessions[session_id]

        # Get response (now includes products!)
        result = bot.chat(user_message, user_info)

        return jsonify({
            'success': True,
            'response': result['message'],
            'products': result['products'],
            'categories': result.get('categories', []),
            'intent': result.get('intent', 'general'),
            'session_id': session_id
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history for a session"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')

        if session_id in sessions:
            sessions[session_id].clear_history()

        return jsonify({
            'success': True,
            'message': 'Conversation cleared'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'db_connected': chatbot.db_connected
    })

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("OVN STORE CHATBOT SERVER")
    print("=" * 50)
    print("Starting server at http://localhost:5000")
    print("Open your browser and go to http://localhost:5000")
    print("=" * 50 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
