"""
Nepali Language Support for OVN Store Chatbot
Detects and processes Roman Nepali (Romanized Nepali/Nepali written in English)
Responds in natural Nepali-English mix for local customers
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# Roman Nepali to English keyword mappings
NEPALI_KEYWORDS: Dict[str, str] = {
    # Greetings
    'namaste': 'hello',
    'namaskar': 'hello',
    'namaskarr': 'hello',
    'k cha': 'how are you',
    'kasto cha': 'how are you',
    'sanchai': 'fine',

    # Common words
    'ho': 'yes',
    'hoo': 'yes',
    'hajur': 'yes',
    'hoina': 'no',
    'chaina': 'no',
    'chha': 'is/have',
    'cha': 'is/have',
    'thik cha': 'okay',
    'thikai': 'okay',
    'huncha': 'okay',

    # Questions
    'kati': 'how much',
    'kata': 'where',
    'kasari': 'how',
    'kina': 'why',
    'kun': 'which',
    'ke': 'what',
    'kahile': 'when',
    'ko': 'who',

    # Shopping related
    'kinnu': 'buy',
    'kinna': 'buy',
    'kinchu': 'will buy',
    'linu': 'take',
    'linchu': 'will take',
    'dinu': 'give',
    'dinus': 'please give',
    'dekhau': 'show',
    'dekhaus': 'please show',
    'dekhaidinus': 'please show',
    'chahinchha': 'need',
    'chahiyo': 'needed',
    'parcha': 'costs/required',
    'pugcha': 'enough',

    # Product related
    'saman': 'product',
    'bastu': 'item',
    'maal': 'goods',
    'naya': 'new',
    'ramro': 'good',
    'mitho': 'nice',
    'sasto': 'cheap',
    'mahango': 'expensive',

    # Order related
    'order': 'order',
    'manga': 'order',
    'mangaunu': 'to order',
    'track': 'track',
    'kata pugyo': 'where is it',
    'aipugyo': 'arrived',
    'aayo': 'came',
    'aaena': 'not came',
    'pathau': 'send',
    'pathaunu': 'to send',

    # Quantity
    'euta': 'one',
    'duita': 'two',
    'tinta': 'three',
    'charta': 'four',
    'panchta': 'five',
    'dherai': 'many',
    'ali': 'some',
    'thori': 'little',

    # Polite words
    'dhanyabad': 'thank you',
    'dhanyabaad': 'thank you',
    'dhanybad': 'thank you',
    'maaf': 'sorry',
    'kshama': 'sorry',
    'please': 'please',
    'kripaya': 'please',

    # Location
    'ghar': 'home',
    'thau': 'place',
    'thauma': 'at place',
    'najik': 'near',
    'tadha': 'far',

    # Payment
    'paisa': 'money',
    'rupiya': 'rupees',
    'tirnu': 'pay',
    'tirchu': 'will pay',
    'cash': 'cash',
    'haat ma': 'in hand/cod',

    # Problem words
    'samasya': 'problem',
    'dikkat': 'problem',
    'garo': 'difficult',
    'thik chaina': 'not okay',
    'bigriyo': 'broken',

    # Bye
    'bye': 'bye',
    'pheri bhetaula': 'see you again',
    'ramro sangha': 'take care'
}

# Common Nepali phrases and their intents
NEPALI_INTENT_PHRASES: Dict[str, List[str]] = {
    'greeting': [
        'namaste', 'namaskar', 'k cha', 'kasto cha', 'hello',
        'hi', 'hajur'
    ],
    'order_tracking': [
        'mero order', 'order kata', 'kata pugyo', 'track garnu',
        'order kaha cha', 'delivery kaha', 'aayo ki aena',
        'kahile auncha', 'order status'
    ],
    'order_placement': [
        'kinnu cha', 'kinna cha', 'linu cha', 'chahinchha',
        'order garnu', 'yo dinus', 'yo linchu', 'mangauchu',
        'buy garnu', 'add to cart'
    ],
    'product_search': [
        'dekhau', 'k cha', 'product haru', 'saman dekhau',
        'k k cha', 'show garnus', 'products', 'yo cha',
        'browse'
    ],
    'flash_sale': [
        'offer', 'sale', 'discount', 'sasto', 'deal',
        'flash sale', 'special offer'
    ],
    'support': [
        'samasya', 'problem', 'help', 'dikkat', 'thik chaina',
        'return', 'refund', 'complaint', 'garo cha'
    ],
    'thanks': [
        'dhanyabad', 'dhanyabaad', 'thank you', 'thanks',
        'dhanybad'
    ],
    'bye': [
        'bye', 'goodbye', 'pheri bhetaula', 'ramro sangha',
        'see you'
    ],
    'policy': [
        'delivery kati din', 'shipping charge', 'return policy',
        'payment kasari', 'cod cha', 'kati parcha delivery'
    ],
    'price': [
        'kati parcha', 'price', 'rate', 'cost', 'kati ho'
    ]
}

# Response templates in Nepali-English mix
NEPALI_RESPONSES: Dict[str, List[str]] = {
    'greeting': [
        "Namaste! OVN Store ma swagat cha! Kasari help garna sakchu?",
        "Namaskar! Aaja k help chahinchha?",
        "Hello! OVN Store ma welcome! K kinna chahanu huncha?"
    ],
    'thanks': [
        "Dhanyabad! Aru kehi help chahinchha?",
        "You're welcome! Pheri aaunus!",
        "Khusi lagyo help garna paayera!"
    ],
    'bye': [
        "Dhanyabad! Pheri bhetaula!",
        "Bye! OVN Store ma pheri aaunu hola!",
        "Ramro sangha! Order ko laagi dhanyabad!"
    ],
    'product_not_found': [
        "Maaf, tyo product bhetiyena. Arko naam le try garnus.",
        "Product khojina sakena. Different keyword try garnus.",
        "Tyo product available chaina. Aru kehi hernu huncha?"
    ],
    'order_ask_identifier': [
        "Order track garna phone number ya order ID dinus.",
        "Tapai ko phone number ki order number dinus, ma track garchu.",
        "Phone number (10 digits) dinus order check garna."
    ],
    'order_found': [
        "Order bhetyo! Yo ho tapai ko order details:",
        "Tapai ko order yaha cha:",
        "Order status yaha hernus:"
    ],
    'order_not_found': [
        "Maaf, order bhetiyena. Order ID check garera feri try garnus.",
        "Tyo order chaina. Number ramrari check garnus.",
        "Order khojina sakena. Different ID try garnus."
    ],
    'product_show': [
        "Yo hera tapai le khojeko products:",
        "Hamro store ma yo products cha:",
        "Yehi products available cha:"
    ],
    'buy_confirm': [
        "Ramro choice! Yo product order garnu huncha?",
        "Nice! Yo kinnu huncha?",
        "Great! Yo add garnu huncha order ma?"
    ],
    'ask_quantity': [
        "Kati wota chahinchha?",
        "Quantity kati ho?",
        "Kati order garnu huncha?"
    ],
    'ask_name': [
        "Tapai ko naam k ho?",
        "Full name dinus please.",
        "Delivery ko laagi naam dinus."
    ],
    'ask_phone': [
        "Phone number dinus (10 digits).",
        "Contact number dinus.",
        "Mobile number k ho tapai ko?"
    ],
    'ask_location': [
        "Delivery kata garne? District ra location dinus.",
        "Address dinus - kun thau ma pathaaune?",
        "Delivery location k ho?"
    ],
    'ask_landmark': [
        "Najik ko landmark k cha? (Skip garna 'skip' type garnus)",
        "Kei landmark cha nearby?",
        "Thau chinne kei cha? (optional)"
    ],
    'order_confirm': [
        "Order summary yo ho. Confirm garnu huncha?",
        "Yeso hernus order details. Thik cha?",
        "Order place garne ho? Confirm garnus."
    ],
    'order_success': [
        "Order successfully place bhayo! Order number: {order_id}. 3-5 din ma delivery huncha.",
        "Dhanyabad! Order #{order_id} confirm bhayo. Cash on Delivery ho.",
        "Great! Order complete. #{order_id} - Delivery 3-5 business days ma."
    ],
    'policy_info': [
        "OVN Store Policies:\n- Rs.1000 mathi free shipping\n- 7 din return policy\n- Cash on Delivery available\n- 3-5 din ma delivery Nepal bhari",
        "Hamro policy:\n- Free delivery Rs.1000+\n- 7 days return\n- COD available\n- Nepal wide delivery"
    ],
    'support_ask': [
        "K samasya cha? Details dinus, help garchu.",
        "Problem k ho? Describe garnus.",
        "Support chahinchha? K bhayo bataunus."
    ],
    'suggestions': [
        "Tapai lai yo products ni man parna sakcha:",
        "Yo pani hera, ramro cha:",
        "Related products:"
    ],
    'fallback': [
        "Maile bujhina. Feri bhannus please?",
        "K bhannu bhako thik bujhina. Arko tarika le bhannus.",
        "Sorry, clear bhayena. Can you rephrase?"
    ]
}


@dataclass
class NepaliDetectionResult:
    """Result of Nepali detection"""
    is_nepali: bool
    confidence: float
    detected_words: List[str]
    translated_text: str


class NepaliDetector:
    """
    Detects if message contains Roman Nepali.
    Uses keyword matching and pattern recognition.
    """

    # Nepali-specific patterns
    NEPALI_PATTERNS = [
        r'\b(cha|chha|huncha|bhayo)\b',  # Common verb endings
        r'\b(ko|ma|lai|le|bata)\b',  # Common postpositions
        r'\b(ho|hoina|chaina)\b',  # Common affirmations/negations
        r'\b(garnu|garna|gareko)\b',  # Common verb forms
        r'\b(ta|ni|pani|chai)\b',  # Common particles
    ]

    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.NEPALI_PATTERNS]

    def detect(self, text: str) -> NepaliDetectionResult:
        """
        Detect if text contains Nepali.

        Args:
            text: Input text

        Returns:
            NepaliDetectionResult with detection info
        """
        if not text:
            return NepaliDetectionResult(False, 0.0, [], text)

        text_lower = text.lower()
        words = text_lower.split()
        detected_words = []
        nepali_score = 0

        # Check for Nepali keywords
        for word in words:
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w]', '', word)

            if clean_word in NEPALI_KEYWORDS:
                detected_words.append(clean_word)
                nepali_score += 2  # Higher weight for known keywords

            # Check for multi-word phrases
            for phrase, _ in NEPALI_KEYWORDS.items():
                if ' ' in phrase and phrase in text_lower:
                    detected_words.append(phrase)
                    nepali_score += 3

        # Check patterns
        for pattern in self.patterns:
            matches = pattern.findall(text_lower)
            for match in matches:
                if match not in detected_words:
                    detected_words.append(match)
                    nepali_score += 1

        # Calculate confidence
        total_words = len(words)
        if total_words == 0:
            confidence = 0.0
        else:
            confidence = min(1.0, nepali_score / (total_words * 2))

        is_nepali = confidence >= 0.2 or len(detected_words) >= 2

        # Translate detected words
        translated_text = self._translate(text_lower, detected_words)

        return NepaliDetectionResult(
            is_nepali=is_nepali,
            confidence=confidence,
            detected_words=detected_words,
            translated_text=translated_text
        )

    def _translate(self, text: str, detected_words: List[str]) -> str:
        """Translate Nepali words to English equivalents"""
        result = text
        for word in detected_words:
            if word in NEPALI_KEYWORDS:
                english = NEPALI_KEYWORDS[word]
                result = result.replace(word, english)
        return result


class NepaliIntentMatcher:
    """
    Matches Nepali phrases to intents.
    """

    def match_intent(self, text: str) -> Tuple[Optional[str], float]:
        """
        Match text to an intent based on Nepali phrases.

        Args:
            text: Input text (already lowercased)

        Returns:
            Tuple of (intent, confidence)
        """
        text_lower = text.lower()
        best_intent = None
        best_score = 0.0

        for intent, phrases in NEPALI_INTENT_PHRASES.items():
            score = 0
            for phrase in phrases:
                if phrase in text_lower:
                    # Longer phrase = higher score
                    score += len(phrase.split()) * 0.3

            if score > best_score:
                best_score = score
                best_intent = intent

        # Normalize score
        confidence = min(1.0, best_score)

        return best_intent, confidence


class NepaliResponder:
    """
    Generates responses in Nepali-English mix.
    """

    def __init__(self):
        self.detector = NepaliDetector()

    def get_response(
        self,
        response_type: str,
        use_nepali: bool = True,
        **kwargs
    ) -> str:
        """
        Get response in appropriate language.

        Args:
            response_type: Type of response (key in NEPALI_RESPONSES)
            use_nepali: Whether to use Nepali response
            **kwargs: Format arguments

        Returns:
            Response string
        """
        import random

        if use_nepali and response_type in NEPALI_RESPONSES:
            responses = NEPALI_RESPONSES[response_type]
        else:
            # Fallback to English (these would be defined elsewhere)
            return self._get_english_fallback(response_type, **kwargs)

        response = random.choice(responses)

        # Format with kwargs
        if kwargs:
            try:
                response = response.format(**kwargs)
            except KeyError:
                pass

        return response

    def _get_english_fallback(self, response_type: str, **kwargs) -> str:
        """English fallback responses"""
        fallbacks = {
            'greeting': "Hello! Welcome to OVN Store! How can I help you?",
            'thanks': "You're welcome! Anything else I can help with?",
            'bye': "Thank you for visiting! Have a great day!",
            'fallback': "I didn't understand that. Could you please rephrase?"
        }
        return fallbacks.get(response_type, fallbacks['fallback'])

    def should_use_nepali(self, text: str) -> bool:
        """Check if response should be in Nepali"""
        result = self.detector.detect(text)
        return result.is_nepali


# Global instances
nepali_detector = NepaliDetector()
nepali_responder = NepaliResponder()
nepali_intent_matcher = NepaliIntentMatcher()


# Convenience functions
def detect_nepali(text: str) -> NepaliDetectionResult:
    """Detect if text contains Nepali"""
    return nepali_detector.detect(text)


def get_nepali_response(response_type: str, **kwargs) -> str:
    """Get Nepali response"""
    return nepali_responder.get_response(response_type, use_nepali=True, **kwargs)


def match_nepali_intent(text: str) -> Tuple[Optional[str], float]:
    """Match Nepali text to intent"""
    return nepali_intent_matcher.match_intent(text)


def translate_nepali_keywords(text: str) -> str:
    """Translate Nepali keywords to English"""
    result = nepali_detector.detect(text)
    return result.translated_text


def should_respond_in_nepali(text: str) -> bool:
    """Check if should respond in Nepali"""
    return nepali_responder.should_use_nepali(text)
