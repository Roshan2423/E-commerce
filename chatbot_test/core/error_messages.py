"""
Friendly Error Messages for OVN Store Chatbot
User-friendly error messages for various error scenarios
"""
from typing import Dict, Optional
import random


# Error message templates with variations for natural feel
FRIENDLY_ERRORS: Dict[str, list] = {
    # Connection errors
    'connection_error': [
        "I'm having trouble connecting right now. Please try again in a moment.",
        "Oops! Connection hiccup. Give me a second and try again.",
        "Having some network issues. Please try again shortly."
    ],

    # Timeout errors
    'timeout': [
        "That took longer than expected. Let me try again...",
        "Sorry, that request timed out. Please try once more.",
        "The response is taking too long. Let's try again."
    ],

    # Rate limiting
    'rate_limited': [
        "Whoa, slow down! Please wait a few seconds before sending more messages.",
        "You're sending messages too fast! Take a breather and try again.",
        "Please wait a moment before sending another message."
    ],

    # Product not found
    'product_not_found': [
        "I couldn't find that product. Try searching with different keywords!",
        "Hmm, no products match that search. Want to try different words?",
        "No results found. Try a different search term."
    ],

    # Order errors
    'order_not_found': [
        "I couldn't find that order. Please check the order ID and try again.",
        "No order found with that ID. Double-check and try again?",
        "That order doesn't exist in our system. Please verify the order number."
    ],

    'order_failed': [
        "There was an issue placing your order. Please try again or contact support.",
        "Something went wrong with your order. Let's try again.",
        "Order couldn't be placed. Please try once more."
    ],

    # Validation errors
    'invalid_phone': [
        "Please enter a valid 10-digit phone number (e.g., 9841234567)",
        "That doesn't look like a valid phone number. Try: 98XXXXXXXX",
        "Invalid phone format. Please use a 10-digit Nepal number."
    ],

    'invalid_email': [
        "Please enter a valid email address (e.g., name@example.com)",
        "That email doesn't look right. Can you check it?",
        "Invalid email format. Please try again."
    ],

    'invalid_order_id': [
        "Please enter a valid order ID",
        "That doesn't look like a valid order number. Check and try again.",
        "Invalid order ID format."
    ],

    # AI/API errors
    'ai_unavailable': [
        "My AI assistant is taking a short break. Using backup mode!",
        "AI is busy right now, but I can still help you!",
        "Switching to quick-response mode. How can I help?"
    ],

    'api_error': [
        "Something went wrong on our end. Please try again.",
        "We hit a small bump. Let's try that again.",
        "Technical hiccup! Please retry your request."
    ],

    # Server errors
    'server_error': [
        "Something went wrong on our end. Our team has been notified.",
        "We're experiencing some issues. Please try again in a moment.",
        "Unexpected error occurred. We're looking into it!"
    ],

    # Input errors
    'empty_message': [
        "Please type a message to continue.",
        "I didn't catch that. What would you like to do?",
        "Your message was empty. How can I help you?"
    ],

    'message_too_long': [
        "That message is too long. Please keep it under 1000 characters.",
        "Whoa, that's a lot! Can you make it shorter?",
        "Message too long. Please shorten it and try again."
    ],

    # Session errors
    'session_expired': [
        "Your session has expired. Let's start fresh!",
        "We lost track of our conversation. Starting over!",
        "Session timeout. How can I help you today?"
    ],

    # Support errors
    'support_failed': [
        "Couldn't submit your support request. Please try again.",
        "Support ticket submission failed. Let's try once more.",
        "Error submitting request. Please retry."
    ],

    # Review errors
    'review_failed': [
        "Couldn't submit your review. Please try again.",
        "Review submission failed. Let's try once more.",
        "Error posting review. Please retry."
    ],

    'cannot_review': [
        "You need to purchase this product before reviewing it.",
        "Reviews are only for verified purchases.",
        "Please buy this product first to leave a review."
    ],

    # General fallback
    'unknown_error': [
        "Something unexpected happened. Please try again.",
        "Oops! An error occurred. Let's try that again.",
        "Hit a snag there. Please retry your request."
    ]
}

# Nepali-friendly error messages (Roman Nepali)
NEPALI_ERRORS: Dict[str, list] = {
    'connection_error': [
        "Connection ma problem chha. Feri try garnus.",
        "Network issue chha. Ali bera ma try garnus."
    ],
    'rate_limited': [
        "Dherai chito message pathaudai hunuhunchha. Ali dhilo garnus.",
        "Bistarai! Kehi second pachi try garnus."
    ],
    'product_not_found': [
        "Tyo product bhetiyena. Arko naam le try garnus.",
        "Product khojina sakena. Different keyword use garnus."
    ],
    'order_not_found': [
        "Order bhetiyena. Order ID check garera feri try garnus.",
        "Tyo order chaina. Number ramrari hernus."
    ],
    'invalid_phone': [
        "Thik phone number dinus (10 digits)",
        "Phone number milena. 98XXXXXXXX format ma dinus."
    ]
}


def get_friendly_error(
    error_type: str,
    use_nepali: bool = False,
    **kwargs
) -> str:
    """
    Get a user-friendly error message.

    Args:
        error_type: Type of error (key in FRIENDLY_ERRORS)
        use_nepali: Use Nepali error if available
        **kwargs: Format arguments for the message

    Returns:
        Friendly error message
    """
    # Try Nepali first if requested
    if use_nepali and error_type in NEPALI_ERRORS:
        messages = NEPALI_ERRORS[error_type]
    else:
        messages = FRIENDLY_ERRORS.get(error_type, FRIENDLY_ERRORS['unknown_error'])

    # Get random variation for natural feel
    message = random.choice(messages)

    # Format with provided arguments if any
    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError:
            pass  # Ignore missing format keys

    return message


def get_error_with_suggestion(
    error_type: str,
    suggestion: str = None,
    use_nepali: bool = False
) -> str:
    """
    Get error message with helpful suggestion.

    Args:
        error_type: Type of error
        suggestion: Additional suggestion to append
        use_nepali: Use Nepali if available

    Returns:
        Error message with suggestion
    """
    message = get_friendly_error(error_type, use_nepali)

    if suggestion:
        message += f"\n\n{suggestion}"

    return message


def get_retry_message(attempt: int, max_attempts: int) -> str:
    """
    Get message for retry attempts.

    Args:
        attempt: Current attempt number
        max_attempts: Maximum attempts

    Returns:
        Retry status message
    """
    if attempt < max_attempts:
        return f"Trying again... (attempt {attempt}/{max_attempts})"
    else:
        return "All attempts failed. Please try again later."


def get_wait_message(seconds: int) -> str:
    """
    Get message for wait time.

    Args:
        seconds: Seconds to wait

    Returns:
        Wait message
    """
    if seconds <= 5:
        return f"Please wait {seconds} seconds..."
    elif seconds <= 30:
        return f"Please wait about {seconds} seconds. Almost there!"
    else:
        return f"Please try again in {seconds // 60} minute(s)."


# Quick access functions
def connection_error(use_nepali: bool = False) -> str:
    return get_friendly_error('connection_error', use_nepali)


def timeout_error() -> str:
    return get_friendly_error('timeout')


def rate_limited(wait_seconds: int = 0, use_nepali: bool = False) -> str:
    msg = get_friendly_error('rate_limited', use_nepali)
    if wait_seconds > 0:
        msg += f" ({wait_seconds}s)"
    return msg


def product_not_found(use_nepali: bool = False) -> str:
    return get_friendly_error('product_not_found', use_nepali)


def order_not_found(use_nepali: bool = False) -> str:
    return get_friendly_error('order_not_found', use_nepali)


def invalid_phone(use_nepali: bool = False) -> str:
    return get_friendly_error('invalid_phone', use_nepali)


def invalid_email() -> str:
    return get_friendly_error('invalid_email')


def server_error() -> str:
    return get_friendly_error('server_error')


def ai_unavailable() -> str:
    return get_friendly_error('ai_unavailable')


# Error response builder for API
def build_error_response(
    error_type: str,
    use_nepali: bool = False,
    include_quick_replies: bool = True
) -> dict:
    """
    Build complete error response for API.

    Args:
        error_type: Type of error
        use_nepali: Use Nepali message
        include_quick_replies: Include helpful quick reply options

    Returns:
        Complete error response dict
    """
    message = get_friendly_error(error_type, use_nepali)

    response = {
        'success': False,
        'error': True,
        'message': message,
        'response': message,
        'error_type': error_type
    }

    if include_quick_replies:
        # Add contextual quick replies based on error type
        if error_type in ['product_not_found']:
            response['quick_replies'] = ['Browse Products', 'Flash Sales', 'Categories']
        elif error_type in ['order_not_found', 'invalid_order_id']:
            response['quick_replies'] = ['Use Phone Number', 'Try Again']
        elif error_type in ['connection_error', 'timeout', 'server_error']:
            response['quick_replies'] = ['Try Again', 'Get Help']
        else:
            response['quick_replies'] = ['Start Over', 'Get Help']

    return response
