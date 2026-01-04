"""
Conversation State Machine for OVN Store Chatbot
Handles state transitions and flow control
"""
from typing import Dict, Optional, Callable, Any
from .session import ConversationState, SessionData


class StateMachine:
    """
    Manages conversation state transitions.
    Determines which handler should process user input based on current state.
    """

    # Define which states belong to which feature
    STATE_GROUPS = {
        'order_tracking': [
            ConversationState.ORDER_TRACKING_START,
            ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER,
            ConversationState.ORDER_TRACKING_SELECTING_ORDER,
        ],
        'order_placement': [
            ConversationState.ORDER_PLACEMENT_START,
            ConversationState.ORDER_PLACEMENT_ASKING_PRODUCT,
            ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT,
            ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT,
            ConversationState.ORDER_PLACEMENT_ASKING_ACTION,
            ConversationState.ORDER_PLACEMENT_SHOWING_DETAILS,
            ConversationState.ORDER_PLACEMENT_AWAITING_QUANTITY,
            ConversationState.ORDER_PLACEMENT_AWAITING_NAME,
            ConversationState.ORDER_PLACEMENT_AWAITING_PHONE,
            ConversationState.ORDER_PLACEMENT_SELECTING_DISTRICT,
            ConversationState.ORDER_PLACEMENT_SELECTING_LOCATION,
            ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK,
            ConversationState.ORDER_PLACEMENT_CONFIRMING,
        ],
        'support': [
            ConversationState.SUPPORT_START,
            ConversationState.SUPPORT_AWAITING_CATEGORY,
            ConversationState.SUPPORT_AWAITING_DETAILS,
            ConversationState.SUPPORT_AWAITING_EMAIL,
            ConversationState.SUPPORT_CONFIRMING,
        ],
        'review': [
            ConversationState.REVIEW_SELECTING_PRODUCT,
            ConversationState.REVIEW_AWAITING_RATING,
            ConversationState.REVIEW_AWAITING_TITLE,
            ConversationState.REVIEW_AWAITING_COMMENT,
            ConversationState.REVIEW_CONFIRMING,
        ]
    }

    # Words that indicate user wants to cancel/go back
    CANCEL_KEYWORDS = ['cancel', 'stop', 'nevermind', 'never mind', 'quit', 'exit', 'go back', 'start over']

    # Words that indicate confirmation
    CONFIRM_KEYWORDS = ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'confirm', 'correct', 'right', 'proceed']

    # Words that indicate rejection
    REJECT_KEYWORDS = ['no', 'nope', 'nah', 'wrong', 'incorrect', 'change', 'different']

    def __init__(self):
        pass

    def get_handler_type(self, state: ConversationState) -> Optional[str]:
        """Get the handler type for a given state"""
        if state == ConversationState.IDLE:
            return None

        for handler_type, states in self.STATE_GROUPS.items():
            if state in states:
                return handler_type
        return None

    def is_in_flow(self, session: SessionData) -> bool:
        """Check if session is in an active multi-step flow"""
        return session.state != ConversationState.IDLE

    def should_cancel(self, message: str) -> bool:
        """Check if user wants to cancel current flow"""
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in self.CANCEL_KEYWORDS)

    def is_confirmation(self, message: str) -> bool:
        """Check if message is a confirmation"""
        message_lower = message.lower().strip()
        # Exact match for short responses
        if message_lower in ['yes', 'y', 'yeah', 'yep', 'ok', 'okay', 'sure', 'confirm']:
            return True
        return any(keyword in message_lower for keyword in self.CONFIRM_KEYWORDS)

    def is_rejection(self, message: str) -> bool:
        """Check if message is a rejection"""
        message_lower = message.lower().strip()
        # Exact match for short responses
        if message_lower in ['no', 'n', 'nope', 'nah', 'cancel']:
            return True
        return any(keyword in message_lower for keyword in self.REJECT_KEYWORDS)

    def get_next_state(self, current_state: ConversationState, success: bool = True) -> ConversationState:
        """
        Get the next state in a flow based on current state.
        Used for automatic state progression.
        """
        # Order Placement Flow
        order_flow = [
            ConversationState.ORDER_PLACEMENT_START,
            ConversationState.ORDER_PLACEMENT_ASKING_PRODUCT,
            ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT,
            ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT,
            ConversationState.ORDER_PLACEMENT_ASKING_ACTION,
            ConversationState.ORDER_PLACEMENT_SHOWING_DETAILS,
            ConversationState.ORDER_PLACEMENT_AWAITING_QUANTITY,
            ConversationState.ORDER_PLACEMENT_AWAITING_NAME,
            ConversationState.ORDER_PLACEMENT_AWAITING_PHONE,
            ConversationState.ORDER_PLACEMENT_SELECTING_DISTRICT,
            ConversationState.ORDER_PLACEMENT_SELECTING_LOCATION,
            ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK,
            ConversationState.ORDER_PLACEMENT_CONFIRMING,
        ]

        # Support Flow
        support_flow = [
            ConversationState.SUPPORT_START,
            ConversationState.SUPPORT_AWAITING_CATEGORY,
            ConversationState.SUPPORT_AWAITING_DETAILS,
            ConversationState.SUPPORT_AWAITING_EMAIL,
            ConversationState.SUPPORT_CONFIRMING,
        ]

        # Review Flow
        review_flow = [
            ConversationState.REVIEW_SELECTING_PRODUCT,
            ConversationState.REVIEW_AWAITING_RATING,
            ConversationState.REVIEW_AWAITING_TITLE,
            ConversationState.REVIEW_AWAITING_COMMENT,
            ConversationState.REVIEW_CONFIRMING,
        ]

        # Find next state in flow
        for flow in [order_flow, support_flow, review_flow]:
            if current_state in flow:
                idx = flow.index(current_state)
                if success and idx < len(flow) - 1:
                    return flow[idx + 1]
                elif not success and idx > 0:
                    return flow[idx - 1]  # Go back
                break

        return ConversationState.IDLE

    def can_skip_state(self, state: ConversationState, session: SessionData) -> bool:
        """
        Check if we can skip a state because we already have the data.
        Used to auto-fill from session memory.
        """
        skip_conditions = {
            ConversationState.ORDER_PLACEMENT_AWAITING_NAME: session.user_name is not None,
            ConversationState.ORDER_PLACEMENT_AWAITING_PHONE: session.user_phone is not None,
            ConversationState.ORDER_PLACEMENT_SELECTING_DISTRICT: session.user_location is not None,
            ConversationState.SUPPORT_AWAITING_EMAIL: session.user_email is not None,
        }
        return skip_conditions.get(state, False)

    def get_state_prompt(self, state: ConversationState) -> str:
        """Get the prompt/question for a given state"""
        prompts = {
            ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER:
                "Please provide your **order ID** or **phone number** to track your order.",

            ConversationState.ORDER_TRACKING_SELECTING_ORDER:
                "Which order would you like to see details for?",

            ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT:
                "Which product would you like to order?",

            ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT:
                "Would you like to order this product?",

            ConversationState.ORDER_PLACEMENT_AWAITING_QUANTITY:
                "How many would you like? (Default: 1)",

            ConversationState.ORDER_PLACEMENT_AWAITING_NAME:
                "What is your name for the delivery?",

            ConversationState.ORDER_PLACEMENT_AWAITING_PHONE:
                "Please provide your phone number (10 digits).",

            ConversationState.ORDER_PLACEMENT_SELECTING_DISTRICT:
                "Select your district for delivery.",

            ConversationState.ORDER_PLACEMENT_SELECTING_LOCATION:
                "Select your location within the district.",

            ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK:
                "Any nearby landmark? (Type 'skip' if none)",

            ConversationState.ORDER_PLACEMENT_CONFIRMING:
                "Please confirm your order. Type 'yes' to place or 'no' to cancel.",

            ConversationState.SUPPORT_AWAITING_CATEGORY:
                "What type of issue do you have?\n1. Order Issue\n2. Product Question\n3. Complaint\n4. Return/Refund\n5. Other",

            ConversationState.SUPPORT_AWAITING_DETAILS:
                "Please describe your issue in detail.",

            ConversationState.SUPPORT_AWAITING_EMAIL:
                "What's your email address so we can respond?",

            ConversationState.SUPPORT_CONFIRMING:
                "Submit this support request?",

            ConversationState.REVIEW_SELECTING_PRODUCT:
                "Which product would you like to review?",

            ConversationState.REVIEW_AWAITING_RATING:
                "How would you rate this product? (1-5 stars)",

            ConversationState.REVIEW_AWAITING_TITLE:
                "Give your review a short title.",

            ConversationState.REVIEW_AWAITING_COMMENT:
                "Write your review comment.",

            ConversationState.REVIEW_CONFIRMING:
                "Submit this review?",
        }
        return prompts.get(state, "")


# Export both from this module
__all__ = ['ConversationState', 'StateMachine']

# Re-export ConversationState
from .session import ConversationState
