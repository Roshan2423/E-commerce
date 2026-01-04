"""
Session Management for OVN Store Chatbot
Handles user session memory and conversation context
Now with MongoDB persistence for chat history
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from enum import Enum
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SESSION_TIMEOUT_MINUTES, MAX_CONVERSATION_HISTORY

# Import persistence layer (lazy loading to avoid circular imports)
_persistence_loaded = False
_session_store = None
_user_memory = None
_analytics_store = None


def _load_persistence():
    """Lazy load persistence layer"""
    global _persistence_loaded, _session_store, _user_memory, _analytics_store
    if not _persistence_loaded:
        try:
            from core.persistence import get_session_store, get_user_memory, get_analytics_store
            _session_store = get_session_store()
            _user_memory = get_user_memory()
            _analytics_store = get_analytics_store()
            _persistence_loaded = True
        except Exception as e:
            print(f"Warning: Could not load persistence layer: {e}")
            _persistence_loaded = True  # Don't retry
    return _session_store, _user_memory, _analytics_store


class ConversationState(Enum):
    """All possible conversation states"""
    # Base state
    IDLE = "idle"

    # Order Tracking states
    ORDER_TRACKING_START = "order_tracking_start"
    ORDER_TRACKING_AWAITING_IDENTIFIER = "order_tracking_awaiting_identifier"
    ORDER_TRACKING_SELECTING_ORDER = "order_tracking_selecting_order"

    # Order Placement states
    ORDER_PLACEMENT_START = "order_placement_start"
    ORDER_PLACEMENT_ASKING_PRODUCT = "order_placement_asking_product"
    ORDER_PLACEMENT_SELECTING_PRODUCT = "order_placement_selecting_product"
    ORDER_PLACEMENT_CONFIRMING_PRODUCT = "order_placement_confirming_product"
    ORDER_PLACEMENT_ASKING_ACTION = "order_placement_asking_action"
    ORDER_PLACEMENT_SHOWING_DETAILS = "order_placement_showing_details"
    ORDER_PLACEMENT_AWAITING_QUANTITY = "order_placement_awaiting_quantity"
    ORDER_PLACEMENT_AWAITING_NAME = "order_placement_awaiting_name"
    ORDER_PLACEMENT_AWAITING_PHONE = "order_placement_awaiting_phone"
    ORDER_PLACEMENT_SELECTING_DISTRICT = "order_placement_selecting_district"
    ORDER_PLACEMENT_SELECTING_LOCATION = "order_placement_selecting_location"
    ORDER_PLACEMENT_AWAITING_LANDMARK = "order_placement_awaiting_landmark"
    ORDER_PLACEMENT_CONFIRMING = "order_placement_confirming"

    # Customer Support states
    SUPPORT_START = "support_start"
    SUPPORT_AWAITING_CATEGORY = "support_awaiting_category"
    SUPPORT_AWAITING_DETAILS = "support_awaiting_details"
    SUPPORT_AWAITING_EMAIL = "support_awaiting_email"
    SUPPORT_CONFIRMING = "support_confirming"

    # Review states
    REVIEW_SELECTING_PRODUCT = "review_selecting_product"
    REVIEW_AWAITING_RATING = "review_awaiting_rating"
    REVIEW_AWAITING_TITLE = "review_awaiting_title"
    REVIEW_AWAITING_COMMENT = "review_awaiting_comment"
    REVIEW_CONFIRMING = "review_confirming"


@dataclass
class SessionData:
    """Stores all data for a user session"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    # Current conversation state
    state: ConversationState = ConversationState.IDLE

    # Context for current multi-step flow
    state_context: Dict[str, Any] = field(default_factory=dict)

    # User information (remembered across conversation)
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    user_location: Optional[str] = None
    user_landmark: Optional[str] = None
    is_logged_in: bool = False
    user_id: Optional[int] = None

    # Cart/selection memory
    selected_products: List[Dict] = field(default_factory=list)
    last_viewed_products: List[Dict] = field(default_factory=list)

    # Conversation history
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Preferences learned from conversation
    preferences: Dict[str, Any] = field(default_factory=dict)

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last N messages
        if len(self.conversation_history) > MAX_CONVERSATION_HISTORY:
            self.conversation_history = self.conversation_history[-MAX_CONVERSATION_HISTORY:]

    def get_recent_history(self, count: int = 6) -> List[Dict]:
        """Get recent conversation history for AI context"""
        return self.conversation_history[-count:]

    def remember_user_info(self, **kwargs):
        """Update user info from conversation"""
        if 'name' in kwargs and kwargs['name']:
            self.user_name = kwargs['name']
        if 'phone' in kwargs and kwargs['phone']:
            self.user_phone = kwargs['phone']
        if 'email' in kwargs and kwargs['email']:
            self.user_email = kwargs['email']
        if 'location' in kwargs and kwargs['location']:
            self.user_location = kwargs['location']
        if 'landmark' in kwargs and kwargs['landmark']:
            self.user_landmark = kwargs['landmark']

    def set_state(self, state: ConversationState, context: Dict = None):
        """Set conversation state with optional context"""
        self.state = state
        if context:
            self.state_context.update(context)

    def reset_state(self):
        """Reset to idle state and clear context"""
        self.state = ConversationState.IDLE
        self.state_context = {}

    def get_context(self, key: str, default=None):
        """Get a value from state context"""
        return self.state_context.get(key, default)

    def set_context(self, key: str, value: Any):
        """Set a value in state context"""
        self.state_context[key] = value

    def add_to_cart(self, product: Dict, quantity: int = 1):
        """Add a product to cart"""
        # Check if already in cart
        for item in self.selected_products:
            if item.get('id') == product.get('id'):
                item['quantity'] = item.get('quantity', 1) + quantity
                return
        # Add new item
        product_copy = product.copy()
        product_copy['quantity'] = quantity
        self.selected_products.append(product_copy)

    def clear_cart(self):
        """Clear the cart"""
        self.selected_products = []

    def to_dict(self) -> Dict:
        """Convert session to dictionary for JSON serialization"""
        return {
            'session_id': self.session_id,
            'state': self.state.value,
            'user_name': self.user_name,
            'user_phone': self.user_phone,
            'is_logged_in': self.is_logged_in,
            'cart_items': len(self.selected_products)
        }

    def to_full_dict(self) -> Dict:
        """Convert session to full dictionary for MongoDB storage"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at,
            'last_activity': self.last_activity,
            'state': self.state.value,
            'state_context': self.state_context,
            'user_name': self.user_name,
            'user_phone': self.user_phone,
            'user_email': self.user_email,
            'user_location': self.user_location,
            'user_landmark': self.user_landmark,
            'is_logged_in': self.is_logged_in,
            'user_id': self.user_id,
            'selected_products': self.selected_products,
            'last_viewed_products': self.last_viewed_products,
            'conversation_history': self.conversation_history,
            'preferences': self.preferences,
            'is_active': True,
            'admin_handling': getattr(self, 'admin_handling', False),
            'admin_id': getattr(self, 'admin_id', None)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionData':
        """Create SessionData from dictionary (MongoDB document)"""
        session = cls(session_id=data.get('session_id', ''))

        # Basic fields
        if data.get('created_at'):
            session.created_at = data['created_at'] if isinstance(data['created_at'], datetime) else datetime.fromisoformat(str(data['created_at']))
        if data.get('last_activity'):
            session.last_activity = data['last_activity'] if isinstance(data['last_activity'], datetime) else datetime.fromisoformat(str(data['last_activity']))

        # State
        state_value = data.get('state', 'idle')
        try:
            session.state = ConversationState(state_value)
        except ValueError:
            session.state = ConversationState.IDLE

        session.state_context = data.get('state_context', {})

        # User info
        user_info = data.get('user_info', {})
        session.user_name = user_info.get('name') or data.get('user_name')
        session.user_phone = user_info.get('phone') or data.get('user_phone')
        session.user_email = user_info.get('email') or data.get('user_email')
        session.user_location = user_info.get('location') or data.get('user_location')
        session.user_landmark = data.get('user_landmark')
        session.is_logged_in = data.get('is_logged_in', False)
        session.user_id = data.get('user_id')

        # Products and history
        session.selected_products = data.get('selected_products', [])
        session.last_viewed_products = data.get('last_viewed_products', [])
        session.conversation_history = data.get('conversation_history', [])
        session.preferences = data.get('preferences', {})

        # Admin handling
        session.admin_handling = data.get('admin_handling', False)
        session.admin_id = data.get('admin_id')

        return session

    def save_to_db(self) -> bool:
        """Save session to MongoDB"""
        session_store, _, _ = _load_persistence()
        if session_store:
            return session_store.save_session(self.to_full_dict())
        return False

    def record_analytics_event(self, event_type: str, intent: str = None, metadata: Dict = None) -> bool:
        """Record analytics event for this session"""
        _, _, analytics_store = _load_persistence()
        if analytics_store:
            return analytics_store.record_event(
                event_type=event_type,
                session_id=self.session_id,
                intent=intent,
                metadata=metadata
            )
        return False


class SessionManager:
    """Manages user sessions with automatic cleanup and MongoDB persistence"""

    def __init__(self, timeout_minutes: int = SESSION_TIMEOUT_MINUTES, use_persistence: bool = True):
        self.sessions: Dict[str, SessionData] = {}
        self.timeout = timedelta(minutes=timeout_minutes)
        self.use_persistence = use_persistence

    def get_or_create(self, session_id: str, phone: str = None) -> SessionData:
        """
        Get existing session or create new one.
        Checks MongoDB first if persistence is enabled.
        Also checks user memory for returning customers.
        """
        self.cleanup_expired()

        # Check in-memory cache first
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.update_activity()
            return session

        # Try to load from MongoDB
        if self.use_persistence:
            session_store, user_memory, _ = _load_persistence()

            # Try to load existing session
            if session_store:
                db_session = session_store.load_session(session_id)
                if db_session:
                    session = SessionData.from_dict(db_session)
                    self.sessions[session_id] = session
                    session.update_activity()
                    return session

            # Check if returning customer by phone
            if phone and user_memory:
                memory = user_memory.get_by_phone(phone)
                if memory:
                    # Create new session with remembered info
                    session = SessionData(session_id=session_id)
                    session.user_name = memory.get('name')
                    session.user_phone = memory.get('phone')
                    session.user_email = memory.get('email')
                    session.user_location = memory.get('preferred_location')
                    session.user_landmark = memory.get('preferred_landmark')
                    session.preferences = {
                        'returning_customer': True,
                        'total_orders': memory.get('total_orders', 0),
                        'categories_interested': memory.get('categories_interested', [])
                    }
                    self.sessions[session_id] = session
                    return session

        # Create new session
        session = SessionData(session_id=session_id)
        self.sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[SessionData]:
        """Get session if exists (memory only)"""
        return self.sessions.get(session_id)

    def delete(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            # Mark as inactive in MongoDB
            if self.use_persistence:
                session_store, _, _ = _load_persistence()
                if session_store:
                    session_store.mark_inactive(session_id)
            del self.sessions[session_id]

    def save_session(self, session_id: str) -> bool:
        """Explicitly save session to MongoDB"""
        if session_id in self.sessions and self.use_persistence:
            return self.sessions[session_id].save_to_db()
        return False

    def save_all_sessions(self) -> int:
        """Save all sessions to MongoDB (useful before shutdown)"""
        saved = 0
        if self.use_persistence:
            for session in self.sessions.values():
                if session.save_to_db():
                    saved += 1
        return saved

    def cleanup_expired(self):
        """Remove sessions older than timeout"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session.last_activity > self.timeout
        ]
        for sid in expired:
            # Save to DB before removing from memory
            if self.use_persistence:
                session = self.sessions[sid]
                session.save_to_db()
            del self.sessions[sid]

    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        self.cleanup_expired()
        return len(self.sessions)

    def get_sessions_by_phone(self, phone: str, limit: int = 10) -> List[Dict]:
        """Get previous sessions for a phone number from MongoDB"""
        if self.use_persistence:
            session_store, _, _ = _load_persistence()
            if session_store:
                return session_store.find_sessions_by_phone(phone, limit)
        return []

    def get_all_active_sessions(self) -> List[SessionData]:
        """Get all active sessions (for admin)"""
        self.cleanup_expired()
        return list(self.sessions.values())

    def set_admin_handling(self, session_id: str, admin_id: int, handling: bool) -> bool:
        """Set admin handling status for a session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.admin_handling = handling
            session.admin_id = admin_id if handling else None

            if self.use_persistence:
                session_store, _, _ = _load_persistence()
                if session_store:
                    return session_store.set_admin_handling(session_id, admin_id, handling)
        return False

    def update_user_memory(self, phone: str, **kwargs) -> bool:
        """Update persistent user memory"""
        if self.use_persistence and phone:
            _, user_memory, _ = _load_persistence()
            if user_memory:
                return user_memory.update(phone=phone, data=kwargs)
        return False

    def record_order(self, phone: str, order_id: str, order_total: float, category: str = None) -> bool:
        """Record an order in user memory"""
        if self.use_persistence and phone:
            _, user_memory, _ = _load_persistence()
            if user_memory:
                return user_memory.record_order(phone, order_id, order_total, category)
        return False
