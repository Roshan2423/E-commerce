"""
Customer Support Handler for OVN Store Chatbot
Handles complaints, returns, and support tickets
"""
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .base import BaseHandler, HandlerResponse
from core.session import SessionData, ConversationState
from config import SUPPORT_CATEGORIES


class SupportHandler(BaseHandler):
    """
    Handles customer support flow:
    1. Identify issue category
    2. Collect issue details
    3. Get contact information
    4. Submit support ticket
    """

    CATEGORY_KEYWORDS = {
        'order': ['order', 'delivery', 'shipping', 'track', 'late', 'delayed', 'missing'],
        'product': ['product', 'item', 'quality', 'size', 'color', 'specs'],
        'complaint': ['complaint', 'bad', 'terrible', 'worst', 'angry', 'disappointed'],
        'return': ['return', 'refund', 'exchange', 'damaged', 'broken', 'defective', 'wrong'],
        'feedback': ['feedback', 'suggestion', 'improve', 'idea'],
        'general': ['help', 'question', 'ask', 'info', 'information']
    }

    def can_handle(self, intent: str, state: ConversationState) -> bool:
        """Handle support intent or active support states"""
        if intent == 'support' and state == ConversationState.IDLE:
            return True
        support_states = [
            ConversationState.SUPPORT_START,
            ConversationState.SUPPORT_AWAITING_CATEGORY,
            ConversationState.SUPPORT_AWAITING_DETAILS,
            ConversationState.SUPPORT_AWAITING_EMAIL,
            ConversationState.SUPPORT_CONFIRMING
        ]
        return state in support_states

    def handle(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process support request"""
        state = session.state

        if state == ConversationState.IDLE:
            return self.start_support(message, session, entities)

        elif state == ConversationState.SUPPORT_AWAITING_CATEGORY:
            return self.process_category(message, session, entities)

        elif state == ConversationState.SUPPORT_AWAITING_DETAILS:
            return self.process_details(message, session, entities)

        elif state == ConversationState.SUPPORT_AWAITING_EMAIL:
            return self.process_email(message, session, entities)

        elif state == ConversationState.SUPPORT_CONFIRMING:
            return self.process_confirmation(message, session, entities)

        return self.start_support(message, session, entities)

    def start_support(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Start support flow - detect category from initial message"""
        # Try to detect category from message
        category = self.detect_category(message)

        if category:
            session.set_context('category', category)
            session.set_state(ConversationState.SUPPORT_AWAITING_DETAILS)

            category_name = SUPPORT_CATEGORIES.get(category, 'General Inquiry')
            return self.response(
                f"I understand you need help with a **{category_name}**.\n\n"
                f"Please describe your issue in detail so we can assist you better.",
                next_state=ConversationState.SUPPORT_AWAITING_DETAILS
            )

        # Show category options
        session.set_state(ConversationState.SUPPORT_AWAITING_CATEGORY)
        return self.response(
            "I'm here to help! What type of issue do you have?\n\n"
            "1. **Order Issue** - Delivery, tracking, missing items\n"
            "2. **Product Question** - Product info, availability\n"
            "3. **Complaint** - Service or quality issues\n"
            "4. **Return/Refund** - Return or get refund\n"
            "5. **Feedback** - Suggestions or ideas\n"
            "6. **Other** - General inquiry",
            next_state=ConversationState.SUPPORT_AWAITING_CATEGORY,
            quick_replies=['Order Issue', 'Return/Refund', 'Complaint', 'Other']
        )

    def detect_category(self, message: str) -> Optional[str]:
        """Detect support category from message"""
        message_lower = message.lower()

        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            # Return category with highest score
            return max(category_scores, key=category_scores.get)

        return None

    def process_category(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process category selection"""
        message_lower = message.lower().strip()

        # Map common responses to categories
        category_map = {
            '1': 'order', 'order': 'order', 'order issue': 'order', 'delivery': 'order',
            '2': 'product', 'product': 'product', 'product question': 'product',
            '3': 'complaint', 'complaint': 'complaint',
            '4': 'return', 'return': 'return', 'refund': 'return', 'return/refund': 'return',
            '5': 'feedback', 'feedback': 'feedback', 'suggestion': 'feedback',
            '6': 'general', 'other': 'general', 'general': 'general'
        }

        category = category_map.get(message_lower, self.detect_category(message))

        if not category:
            category = 'general'

        session.set_context('category', category)
        session.set_state(ConversationState.SUPPORT_AWAITING_DETAILS)

        category_name = SUPPORT_CATEGORIES.get(category, 'General Inquiry')
        prompts = {
            'order': "Please describe your order issue. Include your order number if you have it.",
            'product': "What would you like to know about our products?",
            'complaint': "I'm sorry to hear you're having issues. Please describe what happened.",
            'return': "Please describe what you'd like to return/refund and the reason.",
            'feedback': "We'd love to hear your feedback! Please share your thoughts.",
            'general': "Please describe how we can help you."
        }

        return self.response(
            f"**{category_name}**\n\n{prompts.get(category, prompts['general'])}",
            next_state=ConversationState.SUPPORT_AWAITING_DETAILS
        )

    def process_details(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process issue details"""
        if len(message.strip()) < 10:
            return self.response(
                "Please provide more details so we can help you better.",
                next_state=ConversationState.SUPPORT_AWAITING_DETAILS
            )

        session.set_context('message', message.strip())

        # Check for email
        email = entities.get('email')
        if email:
            session.set_context('email', email)
            session.remember_user_info(email=email)

        if session.user_email:
            session.set_state(ConversationState.SUPPORT_AWAITING_EMAIL)
            return self.response(
                f"Should I use **{session.user_email}** for updates?",
                next_state=ConversationState.SUPPORT_AWAITING_EMAIL,
                quick_replies=['Yes', 'Use different email']
            )

        session.set_state(ConversationState.SUPPORT_AWAITING_EMAIL)
        return self.response(
            "Please provide your email address so we can respond to you.",
            next_state=ConversationState.SUPPORT_AWAITING_EMAIL
        )

    def process_email(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process email input"""
        if self.is_confirmation(message) and session.user_email:
            session.set_context('email', session.user_email)
        else:
            # Extract email
            email = entities.get('email')
            if not email:
                from core.intent import EntityExtractor
                extractor = EntityExtractor()
                email = extractor.extract_email(message)

            if not email or '@' not in email:
                return self.response(
                    "Please provide a valid email address.",
                    next_state=ConversationState.SUPPORT_AWAITING_EMAIL
                )

            session.set_context('email', email)
            session.remember_user_info(email=email)

        # Show summary and confirm
        return self.show_ticket_summary(session)

    def show_ticket_summary(self, session: SessionData) -> HandlerResponse:
        """Show support ticket summary"""
        ctx = session.state_context
        category = ctx.get('category', 'general')
        category_name = SUPPORT_CATEGORIES.get(category, 'General Inquiry')
        message = ctx.get('message', '')[:200]
        email = ctx.get('email', session.user_email)
        phone = session.user_phone or 'Not provided'

        summary = "**Support Ticket Summary**\n\n"
        summary += f"**Category:** {category_name}\n"
        summary += f"**Issue:** {message}...\n"
        summary += f"**Email:** {email}\n"
        summary += f"**Phone:** {phone}\n\n"
        summary += "**Submit this support request?**"

        session.set_state(ConversationState.SUPPORT_CONFIRMING)
        return self.response(
            summary,
            next_state=ConversationState.SUPPORT_CONFIRMING,
            quick_replies=['Submit', 'Cancel']
        )

    def process_confirmation(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process ticket confirmation"""
        if self.is_rejection(message) or 'cancel' in message.lower():
            session.reset_state()
            return self.response(
                "Support request cancelled. Is there anything else I can help with?",
                reset_state=True,
                quick_replies=['Browse Products', 'Track Order']
            )

        if self.is_confirmation(message) or 'submit' in message.lower():
            return self.submit_ticket(session)

        return self.response(
            "Please type 'submit' to send your request or 'cancel' to cancel.",
            next_state=ConversationState.SUPPORT_CONFIRMING,
            quick_replies=['Submit', 'Cancel']
        )

    def submit_ticket(self, session: SessionData) -> HandlerResponse:
        """Submit support ticket to backend"""
        ctx = session.state_context

        contact_data = {
            'name': session.user_name or 'Chat User',
            'email': ctx.get('email', session.user_email),
            'phone': session.user_phone or '',
            'subject': ctx.get('category', 'general'),
            'message': ctx.get('message', '')
        }

        result = self.api.submit_contact(contact_data)
        session.reset_state()

        if result.get('success'):
            ticket_id = result.get('id', 'N/A')
            return self.response(
                f"**Support Request Submitted!** ✅\n\n"
                f"**Reference #:** {ticket_id}\n\n"
                f"Our team will review your request and respond within 24-48 hours to {contact_data['email']}.\n\n"
                f"Thank you for contacting OVN Store!",
                reset_state=True,
                quick_replies=['Browse Products', 'Track Order'],
                metadata={'ticket_id': ticket_id}
            )
        else:
            error = result.get('error', 'Unknown error')
            return self.response(
                f"Sorry, there was an error submitting your request:\n{error}\n\nPlease try again or contact us directly.",
                reset_state=True,
                quick_replies=['Try Again', 'Browse Products']
            )
