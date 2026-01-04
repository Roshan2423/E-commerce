"""
Base Handler for OVN Store Chatbot
All handlers inherit from this class
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.session import SessionData, ConversationState
from api.django_client import DjangoAPIClient
from config import QUICK_REPLIES

# Lazy import AI engine to avoid circular imports
_ai_engine = None

def get_ai_engine():
    global _ai_engine
    if _ai_engine is None:
        from core.ai_engine import AIEngine
        _ai_engine = AIEngine()
    return _ai_engine


@dataclass
class HandlerResponse:
    """Response from a handler"""
    message: str
    products: List[Dict] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    next_state: Optional[ConversationState] = None
    quick_replies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reset_state: bool = False  # If True, reset to IDLE after this response

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON response"""
        return {
            'message': self.message,
            'products': self.products,
            'categories': self.categories,
            'quick_replies': self.quick_replies,
            'metadata': self.metadata
        }


class BaseHandler(ABC):
    """
    Abstract base class for all message handlers.
    Provides common utilities and defines interface.
    """

    def __init__(self, api_client: DjangoAPIClient = None):
        self.api = api_client or DjangoAPIClient()

    @abstractmethod
    def can_handle(self, intent: str, state: ConversationState) -> bool:
        """Check if this handler should process the input"""
        pass

    @abstractmethod
    def handle(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process the user input and return response"""
        pass

    def response(self, message: str, **kwargs) -> HandlerResponse:
        """Create a HandlerResponse with common defaults"""
        return HandlerResponse(
            message=message,
            products=kwargs.get('products', []),
            categories=kwargs.get('categories', []),
            next_state=kwargs.get('next_state'),
            quick_replies=kwargs.get('quick_replies', []),
            metadata=kwargs.get('metadata', {}),
            reset_state=kwargs.get('reset_state', False)
        )

    def is_confirmation(self, message: str) -> bool:
        """Check if message is a confirmation - uses AI for smart understanding"""
        msg = message.lower().strip()

        # Quick exact matches first (no AI needed)
        quick_confirmations = ['yes', 'y', 'yeah', 'yep', 'yup', 'ok', 'okay', 'sure', 'ha', 'ho']
        if msg in quick_confirmations:
            return True

        # For anything else, use AI to interpret
        try:
            ai = get_ai_engine()
            if ai.is_available():
                result = ai.interpret_user_response(message, "confirmation")
                if result.get("type") == "confirmation" and result.get("confidence", 0) > 0.6:
                    return True
        except Exception as e:
            print(f"AI confirmation check error: {e}")

        # Fallback: simple pattern matching
        if len(msg) <= 4 and msg.startswith('y') and msg not in ['you', 'your']:
            return True
        return False

    def is_rejection(self, message: str) -> bool:
        """Check if message is a rejection - uses AI for smart understanding"""
        msg = message.lower().strip()

        # Quick exact matches first (no AI needed)
        quick_rejections = ['no', 'n', 'nope', 'nah', 'cancel', 'hoina']
        if msg in quick_rejections:
            return True

        # For anything else, use AI to interpret
        try:
            ai = get_ai_engine()
            if ai.is_available():
                result = ai.interpret_user_response(message, "rejection")
                if result.get("type") == "rejection" and result.get("confidence", 0) > 0.6:
                    return True
        except Exception as e:
            print(f"AI rejection check error: {e}")

        # Fallback: simple pattern matching
        if len(msg) <= 3 and msg.startswith('n') and msg not in ['new', 'now']:
            return True
        return False

    def is_skip(self, message: str) -> bool:
        """Check if user wants to skip"""
        skips = ['skip', 'none', 'no', 'n/a', 'na', '-', 'nothing']
        return message.lower().strip() in skips

    def format_price(self, price: float) -> str:
        """Format price for display"""
        return f"Rs. {price:,.0f}"

    def format_product_summary(self, product: Dict) -> str:
        """Format product for text display"""
        name = product.get('name', 'Product')[:50]
        price = product.get('price', 0)
        compare = product.get('compare_price', 0)

        text = f"**{name}**\n"
        text += f"Price: {self.format_price(price)}"
        if compare and compare > price:
            text += f" ~~{self.format_price(compare)}~~"

        stock = product.get('stock', 0)
        if stock > 0:
            text += "\nStatus: In Stock"
        else:
            text += "\nStatus: Out of Stock"

        return text

    def format_order_summary(self, order: Dict) -> str:
        """Format order for text display"""
        status_emoji = {
            'processing': '📦', 'confirmed': '✅', 'packed': '📦',
            'shipped': '🚚', 'delivered': '✅', 'cancelled': '❌', 'returned': '↩️'
        }

        order_num = order.get('order_number', order.get('order_id', 'N/A'))
        status = order.get('status', 'unknown')
        emoji = status_emoji.get(status, '')

        text = f"**Order #{order_num}** {emoji}\n"
        text += f"Status: {order.get('status_display', status.title())}\n"
        text += f"Total: {self.format_price(order.get('total_amount', 0))}\n"

        items = order.get('items', [])
        if items:
            text += "\nItems:\n"
            for item in items[:5]:  # Limit to 5 items
                text += f"  • {item.get('product_name', 'Item')} x {item.get('quantity', 1)}\n"

        tracking = order.get('tracking_number')
        if tracking:
            text += f"\nTracking: {tracking}"

        return text

    def ask_with_saved_info(self, session: SessionData, field: str,
                           ask_message: str, next_state: ConversationState) -> HandlerResponse:
        """
        Check if we have saved info and offer to use it, or ask for it.
        """
        field_map = {
            'name': session.user_name,
            'phone': session.user_phone,
            'email': session.user_email,
            'location': session.user_location
        }

        saved_value = field_map.get(field)

        if saved_value:
            return self.response(
                f"I have your {field} as **{saved_value}**. Should I use this?",
                next_state=next_state,
                quick_replies=['Yes', 'No, use different']
            )

        return self.response(
            ask_message,
            next_state=next_state
        )

    def get_quick_replies(self, context: str) -> List[str]:
        """Get quick replies for a context"""
        return QUICK_REPLIES.get(context, [])
