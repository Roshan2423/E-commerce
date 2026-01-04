"""
OVN Store Advanced Chatbot
Main orchestrator for all chatbot functionality
"""
from typing import Dict, List, Optional, Any

# Core modules
from core.session import SessionManager, SessionData, ConversationState
from core.state_machine import StateMachine
from core.intent import IntentDetector, EntityExtractor
from core.ai_engine import AIEngine

# Handlers
from handlers.product import ProductHandler
from handlers.order_tracking import OrderTrackingHandler
from handlers.order_placement import OrderPlacementHandler
from handlers.support import SupportHandler
from handlers.review import ReviewHandler

# API client
from api.django_client import DjangoAPIClient

# Config
from config import RESPONSES, QUICK_REPLIES


class OVNStoreChatbot:
    """
    Advanced chatbot orchestrator.
    Routes messages to appropriate handlers based on intent and state.
    """

    def __init__(self):
        # Initialize core components
        self.session_manager = SessionManager()
        self.state_machine = StateMachine()
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.ai_engine = AIEngine()
        self.api_client = DjangoAPIClient()

        # Initialize handlers
        self.handlers = {
            'product': ProductHandler(self.api_client),
            'order_tracking': OrderTrackingHandler(self.api_client),
            'order_placement': OrderPlacementHandler(self.api_client),
            'support': SupportHandler(self.api_client),
            'review': ReviewHandler(self.api_client)
        }

        # Intent to handler mapping
        self.intent_handler_map = {
            'product_search': 'product',
            'flash_sale': 'product',
            'categories': 'product',
            'product_detail': 'product',
            'order_tracking': 'order_tracking',
            'order_placement': 'order_placement',
            'support': 'support',
            'review_view': 'review',
            'review_submit': 'review'
        }

        print("OVN Store Chatbot initialized!")

    def chat(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Main chat function - processes user message and returns response.

        Args:
            user_message: The user's message
            session_id: Unique session identifier

        Returns:
            Dictionary with message, products, categories, quick_replies, etc.
        """
        # Get or create session
        session = self.session_manager.get_or_create(session_id)

        # Add user message to history
        session.add_message("user", user_message)

        # Check if user wants to cancel current flow
        if self.state_machine.should_cancel(user_message) and self.state_machine.is_in_flow(session):
            session.reset_state()
            return self._build_response(
                "Cancelled. How else can I help you?",
                quick_replies=QUICK_REPLIES.get('greeting', [])
            )

        # Detect intent and extract entities
        intent_result = self.intent_detector.detect(
            user_message,
            session.get_recent_history()
        )
        entity_result = self.entity_extractor.extract(user_message, intent_result.intent)

        # Combine entities with intent info
        entities = entity_result.entities
        entities['intent'] = intent_result.intent
        entities['confidence'] = intent_result.confidence

        # Smart phone number detection - if user just sends a phone number in IDLE state
        # assume they want to track an order
        if session.state == ConversationState.IDLE:
            phone = entities.get('phone')
            clean_msg = user_message.strip()
            # Check if message is primarily a phone number (10 digits, with possible formatting)
            digits_only = ''.join(filter(str.isdigit, clean_msg))
            if phone or (len(digits_only) == 10 and len(clean_msg) <= 15):
                # User sent a phone number - assume order tracking
                intent_result.intent = 'order_tracking'
                entities['intent'] = 'order_tracking'
                if not phone and len(digits_only) == 10:
                    entities['phone'] = digits_only

        # Smart product name detection - triggers for product-like patterns
        # Only when intent is 'general' with very low confidence (greeting/thanks/bye have higher confidence now)
        if session.state == ConversationState.IDLE and intent_result.intent == 'general' and intent_result.confidence < 0.3:
            msg_lower = user_message.lower().strip()
            import re

            # Pattern-based detection for product queries
            product_patterns = [
                r'\d+\s*(ml|l|g|kg|oz|cm|mm|inch)',  # 220ml, 500g, etc.
                r'\d+\s*(pcs|pieces|pack)',  # 3pcs, 10 pack
                r'\d+[a-zA-Z]+',  # 220clover, 40oz (number immediately followed by letters)
                # Product type words - only match if they're the main word (not greetings)
                r'\b(jar|cup|bottle|brush|lamp|toothbrush|bag|phone|stand|clover|stanley|vacuum)\b',
            ]
            is_product_query = any(re.search(pattern, msg_lower) for pattern in product_patterns)

            if is_product_query:
                intent_result.intent = 'product_search'
                entities['intent'] = 'product_search'
                intent_result.confidence = 0.7

        # Determine which handler to use
        handler = self._get_handler(intent_result.intent, session.state)

        if handler:
            # Process with appropriate handler
            response = handler.handle(user_message, session, entities)

            # Update session state if needed
            if response.next_state:
                session.set_state(response.next_state)
            if response.reset_state:
                session.reset_state()

            # Add assistant message to history
            session.add_message("assistant", response.message)

            return self._build_response(
                response.message,
                products=response.products,
                categories=response.categories,
                quick_replies=response.quick_replies,
                intent=intent_result.intent,
                metadata=response.metadata
            )

        # Handle general intents without specific handler
        return self._handle_general_intent(user_message, intent_result.intent, session, entities)

    def _get_handler(self, intent: str, state: ConversationState):
        """Get the appropriate handler for intent and state"""
        # First check if we're in an active flow
        if state != ConversationState.IDLE:
            handler_type = self.state_machine.get_handler_type(state)
            if handler_type and handler_type in self.handlers:
                return self.handlers[handler_type]

        # Check intent mapping
        handler_type = self.intent_handler_map.get(intent)
        if handler_type and handler_type in self.handlers:
            handler = self.handlers[handler_type]
            if handler.can_handle(intent, state):
                return handler

        return None

    def _handle_general_intent(self, message: str, intent: str, session: SessionData, entities: Dict) -> Dict:
        """Handle general intents that don't need specific handlers"""

        if intent == 'greeting':
            response = RESPONSES.get('greeting', "Hello! How can I help you?")
            session.add_message("assistant", response)
            return self._build_response(
                response,
                quick_replies=QUICK_REPLIES.get('greeting', []),
                intent='greeting'
            )

        elif intent == 'thanks':
            response = RESPONSES.get('thanks', "You're welcome!")
            session.add_message("assistant", response)
            return self._build_response(response, intent='thanks')

        elif intent == 'bye':
            response = RESPONSES.get('bye', "Goodbye!")
            session.add_message("assistant", response)
            return self._build_response(response, intent='bye')

        elif intent == 'policy':
            response = """📋 **OVN Store Policies:**

• 🚚 **Free Shipping:** On orders above Rs. 1,000
• ↩️ **Return Policy:** 7-day return for unused items
• 💰 **Payment:** Cash on Delivery available
• 📅 **Delivery:** 3-5 business days in Nepal

How else can I help you?"""
            session.add_message("assistant", response)
            return self._build_response(
                response,
                quick_replies=['Browse Products', 'Track Order'],
                intent='policy'
            )

        # Smart fallback for any unexpected/unusual questions
        return self._handle_unexpected_question(message, intent, session, entities)

    def _handle_unexpected_question(self, message: str, intent: str, session: SessionData, entities: Dict) -> Dict:
        """
        Handler for unexpected/unusual questions.
        Uses fast AI response or pattern-based fallback.
        """
        # First try pattern-based response (instant, no AI needed)
        # Check for specific hardcoded responses first
        pattern_response = self._get_friendly_fallback(message)
        if pattern_response:
            session.add_message("assistant", pattern_response)
            return self._build_response(pattern_response)

        # Use AI for intelligent responses
        if self.ai_engine.is_available():
            # Use fast mode - quick response
            ai_response = self.ai_engine.generate_response(
                message,
                context=session.state_context,
                intent=intent,
                fast_mode=True
            )
            session.add_message("assistant", ai_response)
            return self._build_response(ai_response)

        # Fallback if AI not available
        fallback = "🤔 I'm not sure how to help with that. I can help you browse products, track orders, or place new orders. What would you like to do?"
        session.add_message("assistant", fallback)
        return self._build_response(fallback)

    def _get_friendly_fallback(self, message: str) -> str:
        """Get a friendly fallback response - returns None to let AI handle most queries"""
        message_lower = message.lower()

        # Only handle VERY specific store-related questions with hardcoded answers
        # Let AI handle everything else for intelligent responses

        # Store location question (we're online only)
        if any(phrase in message_lower for phrase in ['where is your store', 'your shop location', 'physical store', 'visit your shop']):
            return "📍 OVN Store is an online store! We deliver across Nepal within 3-5 business days. You can browse products and order directly through this chat."

        # Payment method question
        if any(phrase in message_lower for phrase in ['payment method', 'how to pay', 'accept card', 'online payment']):
            return "💰 We accept Cash on Delivery (COD) only. You pay when your order arrives - no advance payment needed!"

        # Who are you / what is this (about the bot itself)
        if any(phrase in message_lower for phrase in ['who are you', 'what are you', 'are you a bot', 'are you human', 'what is ovn']):
            return "🤖 I'm OVN Store's AI shopping assistant! I can help you find products, place orders, track deliveries, and answer questions. What would you like to do?"

        # Return None for everything else - let AI handle it
        return None

    def _build_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """Build standardized response dictionary"""
        return {
            'success': True,
            'response': message,
            'message': message,  # Alias for compatibility
            'products': kwargs.get('products', []),
            'categories': kwargs.get('categories', []),
            'quick_replies': kwargs.get('quick_replies', []),
            'intent': kwargs.get('intent', 'general'),
            'metadata': kwargs.get('metadata', {}),
            'session_id': kwargs.get('session_id', 'default')
        }

    def get_session_info(self, session_id: str) -> Dict:
        """Get session information for debugging"""
        session = self.session_manager.get(session_id)
        if session:
            return session.to_dict()
        return {'session_id': session_id, 'exists': False}

    def clear_session(self, session_id: str) -> str:
        """Clear a session"""
        self.session_manager.delete(session_id)
        return "Session cleared!"

    def get_active_sessions(self) -> int:
        """Get count of active sessions"""
        return self.session_manager.get_active_sessions_count()


# For backward compatibility and testing
if __name__ == "__main__":
    bot = OVNStoreChatbot()

    print("\n" + "="*50)
    print("OVN Store Chatbot - Testing")
    print("="*50)

    test_messages = [
        "Hello!",
        "Show me all products",
        "I want to buy the vacuum cup",
        "Track my order",
        "I have a complaint",
        "Reviews for pet brush"
    ]

    for msg in test_messages:
        print(f"\nUser: {msg}")
        result = bot.chat(msg)
        print(f"Bot: {result['message'][:200]}...")
        if result['products']:
            print(f"     (Showing {len(result['products'])} products)")
        if result['quick_replies']:
            print(f"     Quick replies: {result['quick_replies']}")
