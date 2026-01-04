"""
Intent Detection and Entity Extraction for OVN Store Chatbot
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import INTENT_KEYWORDS, ENTITY_PATTERNS


@dataclass
class IntentResult:
    """Result of intent detection"""
    intent: str
    confidence: float
    sub_intent: Optional[str] = None
    matched_keywords: List[str] = None

    def __post_init__(self):
        if self.matched_keywords is None:
            self.matched_keywords = []


@dataclass
class EntityResult:
    """Result of entity extraction"""
    entities: Dict[str, Any]
    raw_matches: Dict[str, List[str]]


class IntentDetector:
    """
    Detects user intent from messages.
    Uses keyword matching with confidence scoring.
    """

    def __init__(self):
        self.intent_keywords = INTENT_KEYWORDS

    def detect(self, message: str, conversation_history: List[Dict] = None) -> IntentResult:
        """
        Detect intent from user message.
        Returns IntentResult with intent, confidence, and matched keywords.
        Uses fuzzy matching to handle typos.
        """
        message_lower = message.lower().strip()
        # Clean message - remove extra spaces between words for fuzzy matching
        message_cleaned = ' '.join(message_lower.split())
        best_intent = 'general'
        best_confidence = 0.0
        best_matches = []

        # Check each intent - collect exact and fuzzy matches separately
        intent_scores = {}

        for intent, keywords in self.intent_keywords.items():
            exact_matches = []
            fuzzy_matches = []

            for keyword in keywords:
                # First try exact match
                if keyword in message_lower:
                    exact_matches.append(keyword)
                # Only try fuzzy match if no exact match AND keyword is multi-word
                elif len(keyword) > 4 and ' ' in keyword:
                    fuzzy_score = self._fuzzy_match(keyword, message_cleaned)
                    if fuzzy_score >= 0.85:  # Stricter threshold for fuzzy
                        fuzzy_matches.append(keyword)

            # Prioritize exact matches heavily
            if exact_matches:
                # Big bonus for exact matches
                confidence = self._calculate_confidence(exact_matches, message_lower, intent)
                confidence += 0.2  # Exact match bonus
                intent_scores[intent] = (confidence, exact_matches, True)
            elif fuzzy_matches:
                confidence = self._calculate_confidence(fuzzy_matches, message_lower, intent)
                intent_scores[intent] = (confidence, fuzzy_matches, False)

        # Select best intent - prefer exact matches over fuzzy
        for intent, (confidence, matches, is_exact) in intent_scores.items():
            # If current best is fuzzy but this is exact with decent confidence, prefer exact
            if is_exact and confidence > 0.5:
                if confidence > best_confidence or (not hasattr(self, '_best_is_exact') or not self._best_is_exact):
                    best_confidence = confidence
                    best_intent = intent
                    best_matches = matches
                    self._best_is_exact = True
            elif confidence > best_confidence and not getattr(self, '_best_is_exact', False):
                best_confidence = confidence
                best_intent = intent
                best_matches = matches
                self._best_is_exact = is_exact

        # Reset for next call
        self._best_is_exact = False

        # Boost confidence based on conversation context
        if conversation_history and len(conversation_history) > 0:
            context_boost = self._get_context_boost(best_intent, conversation_history)
            best_confidence = min(1.0, best_confidence + context_boost)

        # Map to handler intents
        best_intent = self._map_to_handler_intent(best_intent)

        return IntentResult(
            intent=best_intent,
            confidence=best_confidence,
            matched_keywords=best_matches
        )

    def _fuzzy_match(self, keyword: str, message: str) -> float:
        """
        Check if keyword fuzzy-matches any part of the message.
        Returns similarity score (0.0 to 1.0).
        Handles typos like "check my orde rplease" matching "check my order"
        """
        keyword_len = len(keyword)

        # Try sliding window approach for multi-word keywords
        words = message.split()
        message_no_spaces = message.replace(' ', '')

        # Check against message without spaces (handles "orde r" -> "order")
        keyword_no_spaces = keyword.replace(' ', '')
        for i in range(len(message_no_spaces) - len(keyword_no_spaces) + 1):
            chunk = message_no_spaces[i:i + len(keyword_no_spaces)]
            ratio = SequenceMatcher(None, keyword_no_spaces, chunk).ratio()
            if ratio >= 0.85:
                return ratio

        # Check with spaces for phrase matching
        for i in range(len(message) - keyword_len + 1):
            chunk = message[i:i + keyword_len + 3]  # Small buffer for typos
            ratio = SequenceMatcher(None, keyword, chunk[:keyword_len]).ratio()
            if ratio >= 0.8:
                return ratio

        # Check individual word combinations for multi-word keywords
        keyword_words = keyword.split()
        if len(keyword_words) > 1:
            for i in range(len(words) - len(keyword_words) + 1):
                phrase = ' '.join(words[i:i + len(keyword_words)])
                ratio = SequenceMatcher(None, keyword, phrase).ratio()
                if ratio >= 0.75:
                    return ratio

        return 0.0

    def _calculate_confidence(self, matches: List[str], message: str, intent: str) -> float:
        """Calculate confidence score for matches"""
        # Base confidence from number of matches
        base_score = min(0.5, len(matches) * 0.2)

        # Specificity bonus - longer matches are more specific and should win
        # This ensures "show reviews" beats "show" for product_search
        longest_match = max(len(m) for m in matches) if matches else 0
        total_match_length = sum(len(m) for m in matches)

        # Heavy bonus for multi-word matches (more specific)
        multi_word_bonus = 0.0
        for m in matches:
            word_count = len(m.split())
            if word_count >= 3:
                multi_word_bonus += 0.25  # Big bonus for 3+ word phrases
            elif word_count == 2:
                multi_word_bonus += 0.15  # Good bonus for 2-word phrases

        specificity = min(0.3, total_match_length / max(len(message), 1) * 0.5)

        # Intent-specific bonuses for high-value intents
        intent_bonus = 0.0
        if intent in ['order_tracking', 'order_placement', 'support', 'review_view', 'review_submit']:
            intent_bonus = 0.1

        # Greetings are naturally short - boost confidence for exact matches
        if intent == 'greeting':
            intent_bonus += 0.35  # Strong boost to prevent product search override

        # Exact phrase match bonus
        if any(m in message for m in matches if len(m) > 10):
            intent_bonus += 0.15  # Longer exact match = higher confidence

        return min(1.0, base_score + specificity + intent_bonus + multi_word_bonus)

    def _get_context_boost(self, intent: str, history: List[Dict]) -> float:
        """Boost confidence based on conversation context"""
        # If user was just shown products and now wants to buy, boost
        if not history:
            return 0.0

        last_messages = history[-2:] if len(history) >= 2 else history
        for msg in last_messages:
            content = msg.get('content', '').lower()
            if 'product' in content or 'found' in content:
                if intent == 'order_placement':
                    return 0.15
                if intent == 'review_view':
                    return 0.1
        return 0.0

    def _map_to_handler_intent(self, intent: str) -> str:
        """Map detected intent to handler intent"""
        intent_map = {
            'order_tracking': 'order_tracking',
            'order_placement': 'order_placement',
            'support': 'support',
            'review_view': 'review_view',
            'review_submit': 'review_submit',
            'product_search': 'product_search',
            'flash_sale': 'flash_sale',
            'categories': 'categories',
            'greeting': 'greeting',
            'policy': 'policy',
            'thanks': 'thanks',
            'bye': 'bye',
            'general': 'general'
        }
        return intent_map.get(intent, 'general')

    def is_product_query(self, message: str) -> bool:
        """Check if message is asking about products"""
        product_indicators = [
            'product', 'show', 'find', 'search', 'looking for',
            'buy', 'price', 'cost', 'how much', 'available'
        ]
        message_lower = message.lower()
        return any(ind in message_lower for ind in product_indicators)


class EntityExtractor:
    """
    Extracts entities (phone, email, order ID, etc.) from messages.
    """

    def __init__(self):
        self.patterns = ENTITY_PATTERNS

    def extract(self, message: str, intent: str = None) -> EntityResult:
        """
        Extract all entities from message.
        Returns EntityResult with parsed entities.
        """
        entities = {}
        raw_matches = {}

        # Phone number (Nepal format)
        phone_matches = re.findall(self.patterns['phone_nepal'], message)
        if phone_matches:
            raw_matches['phone'] = phone_matches
            entities['phone'] = phone_matches[0] if len(phone_matches) == 1 else phone_matches

        # Order ID (short format)
        order_short = re.findall(self.patterns['order_id_short'], message, re.IGNORECASE)
        if order_short:
            raw_matches['order_id_short'] = order_short
            entities['order_id'] = order_short[0].upper()

        # Order UUID (full format)
        order_uuid = re.findall(self.patterns['order_uuid'], message, re.IGNORECASE)
        if order_uuid:
            raw_matches['order_uuid'] = order_uuid
            entities['order_id'] = order_uuid[0]

        # Rating (1-5)
        rating_matches = re.findall(self.patterns['rating'], message, re.IGNORECASE)
        if rating_matches:
            raw_matches['rating'] = rating_matches
            rating = int(rating_matches[0])
            if 1 <= rating <= 5:
                entities['rating'] = rating

        # Quantity
        qty_matches = re.findall(self.patterns['quantity'], message, re.IGNORECASE)
        if qty_matches:
            raw_matches['quantity'] = qty_matches
            try:
                qty = int(qty_matches[0])
                if 1 <= qty <= 100:  # Reasonable limit
                    entities['quantity'] = qty
            except ValueError:
                pass

        # Price
        price_matches = re.findall(self.patterns['price'], message, re.IGNORECASE)
        if price_matches:
            raw_matches['price'] = price_matches
            try:
                price = int(price_matches[0].replace(',', ''))
                entities['max_price'] = price
            except ValueError:
                pass

        # Email
        email_matches = re.findall(self.patterns['email'], message, re.IGNORECASE)
        if email_matches:
            raw_matches['email'] = email_matches
            entities['email'] = email_matches[0]

        return EntityResult(entities=entities, raw_matches=raw_matches)

    def extract_phone(self, message: str) -> Optional[str]:
        """Extract phone number from message"""
        matches = re.findall(self.patterns['phone_nepal'], message)
        return matches[0] if matches else None

    def extract_email(self, message: str) -> Optional[str]:
        """Extract email from message"""
        matches = re.findall(self.patterns['email'], message, re.IGNORECASE)
        return matches[0] if matches else None

    def extract_rating(self, message: str) -> Optional[int]:
        """Extract rating (1-5) from message"""
        # First check for explicit ratings
        matches = re.findall(self.patterns['rating'], message, re.IGNORECASE)
        if matches:
            try:
                rating = int(matches[0])
                if 1 <= rating <= 5:
                    return rating
            except ValueError:
                pass

        # Check for word-based ratings
        message_lower = message.lower()
        word_ratings = {
            'one': 1, '1': 1,
            'two': 2, '2': 2,
            'three': 3, '3': 3,
            'four': 4, '4': 4,
            'five': 5, '5': 5
        }
        for word, rating in word_ratings.items():
            if word in message_lower:
                return rating

        return None

    def extract_quantity(self, message: str) -> Optional[int]:
        """Extract quantity from message"""
        matches = re.findall(self.patterns['quantity'], message, re.IGNORECASE)
        if matches:
            try:
                qty = int(matches[0])
                if 1 <= qty <= 100:
                    return qty
            except ValueError:
                pass

        # Check for word-based quantities
        message_lower = message.lower()
        word_quantities = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        for word, qty in word_quantities.items():
            if word in message_lower:
                return qty

        return None

    def extract_product_keywords(self, message: str) -> List[str]:
        """Extract potential product keywords from message"""
        # Remove common stop words
        stop_words = {
            'show', 'me', 'the', 'a', 'an', 'i', 'want', 'need', 'find', 'search',
            'looking', 'for', 'can', 'you', 'please', 'what', 'do', 'have', 'products',
            'product', 'all', 'everything', 'browse', 'see', 'buy', 'get', 'order',
            'purchase', 'tell', 'about', 'more', 'details', 'info', 'is', 'are',
            'to', 'and', 'or', 'with', 'of', 'in', 'on', 'at', 'by', 'from'
        }

        # Extract words
        words = re.findall(r'\b\w+\b', message.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords
