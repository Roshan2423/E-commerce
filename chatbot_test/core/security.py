"""
Security Module for OVN Store Chatbot
Handles rate limiting, input sanitization, and validation
"""
import re
import html
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from collections import defaultdict
import threading


class RateLimiter:
    """
    Token bucket rate limiter.
    Limits requests per session to prevent spam/abuse.
    """

    def __init__(self, requests_per_minute: int = 30, burst_size: int = 5):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum sustained requests per minute
            burst_size: Maximum burst requests allowed
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens_per_second = requests_per_minute / 60.0

        # Token buckets per session
        self._buckets: Dict[str, Dict] = defaultdict(lambda: {
            'tokens': burst_size,
            'last_update': time.time()
        })
        self._lock = threading.Lock()

        # Cleanup old buckets periodically
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _refill_tokens(self, bucket: Dict) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - bucket['last_update']
        bucket['tokens'] = min(
            self.burst_size,
            bucket['tokens'] + elapsed * self.tokens_per_second
        )
        bucket['last_update'] = now

    def _cleanup_old_buckets(self) -> None:
        """Remove buckets that haven't been used recently"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        with self._lock:
            cutoff = now - 600  # 10 minutes
            to_remove = [
                key for key, bucket in self._buckets.items()
                if bucket['last_update'] < cutoff
            ]
            for key in to_remove:
                del self._buckets[key]
            self._last_cleanup = now

    def check_rate_limit(self, session_id: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for session.

        Args:
            session_id: Unique session identifier

        Returns:
            Tuple of (allowed: bool, wait_seconds: int)
        """
        self._cleanup_old_buckets()

        with self._lock:
            bucket = self._buckets[session_id]
            self._refill_tokens(bucket)

            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True, 0
            else:
                # Calculate wait time
                wait_seconds = int((1 - bucket['tokens']) / self.tokens_per_second) + 1
                return False, wait_seconds

    def get_remaining_requests(self, session_id: str) -> int:
        """Get remaining requests for a session"""
        with self._lock:
            bucket = self._buckets[session_id]
            self._refill_tokens(bucket)
            return int(bucket['tokens'])


class InputSanitizer:
    """
    Sanitizes user input to prevent XSS, injection attacks, etc.
    """

    # Maximum message length
    MAX_MESSAGE_LENGTH = 1000

    # Patterns to remove
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'data:text/html',  # Data URLs
    ]

    # Compiled patterns
    _patterns = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in DANGEROUS_PATTERNS]

    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        Sanitize user input text.

        Args:
            text: Raw user input

        Returns:
            Sanitized text safe for processing
        """
        if not text:
            return ""

        # Truncate to max length
        text = text[:cls.MAX_MESSAGE_LENGTH]

        # Remove dangerous patterns
        for pattern in cls._patterns:
            text = pattern.sub('', text)

        # Escape HTML entities
        text = html.escape(text)

        # Remove null bytes
        text = text.replace('\x00', '')

        # Normalize whitespace
        text = ' '.join(text.split())

        return text.strip()

    @classmethod
    def sanitize_for_display(cls, text: str) -> str:
        """
        Sanitize text for display (allows some formatting).
        Less strict than sanitize().
        """
        if not text:
            return ""

        # Remove script tags and event handlers
        for pattern in cls._patterns:
            text = pattern.sub('', text)

        # Remove null bytes
        text = text.replace('\x00', '')

        return text.strip()


class PhoneValidator:
    """
    Validates Nepal phone numbers.
    Formats: 98XXXXXXXX, 97XXXXXXXX, 96XXXXXXXX, 01XXXXXXXX
    """

    # Nepal phone number pattern
    PATTERN = re.compile(r'^(98|97|96|01)\d{8}$')

    # Pattern to extract phone from text
    EXTRACT_PATTERN = re.compile(r'(?:^|[^\d])((?:98|97|96|01)\d{8})(?:[^\d]|$)')

    @classmethod
    def is_valid(cls, phone: str) -> bool:
        """Check if phone number is valid Nepal format"""
        if not phone:
            return False

        # Remove common separators
        cleaned = re.sub(r'[-\s+()]', '', phone)

        # Remove country code if present
        if cleaned.startswith('977'):
            cleaned = cleaned[3:]
        if cleaned.startswith('+977'):
            cleaned = cleaned[4:]

        return bool(cls.PATTERN.match(cleaned))

    @classmethod
    def normalize(cls, phone: str) -> Optional[str]:
        """
        Normalize phone number to standard format.
        Returns None if invalid.
        """
        if not phone:
            return None

        # Remove common separators
        cleaned = re.sub(r'[-\s+()]', '', phone)

        # Remove country code if present
        if cleaned.startswith('977'):
            cleaned = cleaned[3:]
        if cleaned.startswith('+977'):
            cleaned = cleaned[4:]

        if cls.PATTERN.match(cleaned):
            return cleaned
        return None

    @classmethod
    def extract_from_text(cls, text: str) -> Optional[str]:
        """Extract phone number from text"""
        if not text:
            return None

        match = cls.EXTRACT_PATTERN.search(text)
        if match:
            return match.group(1)
        return None


class EmailValidator:
    """
    Validates email addresses.
    """

    PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    @classmethod
    def is_valid(cls, email: str) -> bool:
        """Check if email is valid format"""
        if not email:
            return False
        return bool(cls.PATTERN.match(email.strip()))

    @classmethod
    def normalize(cls, email: str) -> Optional[str]:
        """Normalize email to lowercase"""
        if not email:
            return None
        email = email.strip().lower()
        if cls.is_valid(email):
            return email
        return None


class OrderIdValidator:
    """
    Validates order IDs.
    Supports: 8-char hex (e.g., ABC12345) or UUID format
    """

    SHORT_PATTERN = re.compile(r'^[A-Fa-f0-9]{8}$')
    UUID_PATTERN = re.compile(
        r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
        re.IGNORECASE
    )

    @classmethod
    def is_valid(cls, order_id: str) -> bool:
        """Check if order ID is valid format"""
        if not order_id:
            return False
        order_id = order_id.strip()
        return bool(cls.SHORT_PATTERN.match(order_id) or cls.UUID_PATTERN.match(order_id))

    @classmethod
    def normalize(cls, order_id: str) -> Optional[str]:
        """Normalize order ID"""
        if not order_id:
            return None
        order_id = order_id.strip().upper()
        if cls.SHORT_PATTERN.match(order_id):
            return order_id
        # For UUID, return lowercase
        if cls.UUID_PATTERN.match(order_id):
            return order_id.lower()
        return None


class SecurityMiddleware:
    """
    Combined security middleware for Flask endpoints.
    """

    def __init__(self, requests_per_minute: int = 30):
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.sanitizer = InputSanitizer()

    def process_request(self, session_id: str, message: str) -> Tuple[bool, str, Optional[str]]:
        """
        Process incoming request through security checks.

        Args:
            session_id: Session identifier
            message: Raw user message

        Returns:
            Tuple of (allowed: bool, sanitized_message: str, error_message: Optional[str])
        """
        # Rate limit check
        allowed, wait_seconds = self.rate_limiter.check_rate_limit(session_id)
        if not allowed:
            return False, "", f"Please slow down! Try again in {wait_seconds} seconds."

        # Sanitize message
        sanitized = self.sanitizer.sanitize(message)

        if not sanitized:
            return False, "", "Please enter a valid message."

        return True, sanitized, None

    def validate_phone(self, phone: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and normalize phone number.

        Returns:
            Tuple of (valid: bool, normalized: Optional[str], error: Optional[str])
        """
        normalized = PhoneValidator.normalize(phone)
        if normalized:
            return True, normalized, None
        return False, None, "Please enter a valid 10-digit phone number (e.g., 9841234567)"

    def validate_email(self, email: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and normalize email.

        Returns:
            Tuple of (valid: bool, normalized: Optional[str], error: Optional[str])
        """
        normalized = EmailValidator.normalize(email)
        if normalized:
            return True, normalized, None
        return False, None, "Please enter a valid email address"

    def validate_order_id(self, order_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and normalize order ID.

        Returns:
            Tuple of (valid: bool, normalized: Optional[str], error: Optional[str])
        """
        normalized = OrderIdValidator.normalize(order_id)
        if normalized:
            return True, normalized, None
        return False, None, "Please enter a valid order ID"


# Global security middleware instance
security_middleware = SecurityMiddleware()


def check_rate_limit(session_id: str) -> Tuple[bool, int]:
    """Convenience function for rate limit check"""
    return security_middleware.rate_limiter.check_rate_limit(session_id)


def sanitize_input(text: str) -> str:
    """Convenience function for input sanitization"""
    return InputSanitizer.sanitize(text)


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Convenience function for phone validation"""
    valid, normalized, _ = security_middleware.validate_phone(phone)
    return valid, normalized


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Convenience function for email validation"""
    valid, normalized, _ = security_middleware.validate_email(email)
    return valid, normalized
