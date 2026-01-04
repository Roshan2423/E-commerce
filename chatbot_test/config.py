"""
Configuration settings for OVN Store Chatbot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ovn_store")

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"  # For complex queries
GROQ_MODEL_FAST = "llama-3.1-8b-instant"  # For quick responses

# Django Backend API
DJANGO_BASE_URL = os.getenv("DJANGO_BASE_URL", "http://localhost:8000")

# Session Configuration
SESSION_TIMEOUT_MINUTES = 30
MAX_CONVERSATION_HISTORY = 20

# Store Information
STORE_INFO = {
    "name": "OVN Store",
    "free_shipping_threshold": 1000,
    "return_days": 7,
    "delivery_days": "3-5",
    "payment_methods": ["Cash on Delivery"],
    "currency": "Rs."
}

# Intent Keywords - Order matters! More specific patterns first get higher confidence
INTENT_KEYWORDS = {
    'order_tracking': [
        'track order', 'track my order', 'where is my order', 'order status',
        'check order', 'check my order', 'find order', 'find my order',
        'order location', 'delivery status', 'order update', 'order kaha',
        'mero order', 'where order', 'status of order', 'order check',
        'track delivery', 'track product delivery', 'where is order',
        'order kati pugyo', 'order aayo', 'delivery kaha pugyo'
    ],
    'order_placement': [
        'buy', 'purchase', 'want to buy', 'add to cart',
        'get this', 'ill take', "i'll take", 'place order', 'order this',
        'buy this', 'purchase this', 'i will buy', 'want this',
        'want to order', 'i want to order', 'like to order', 'like to buy',
        'order now', 'buy now', 'kinchu', 'kinna', 'kinnu', 'yo kinna',
        'checkout', 'proceed to buy'
    ],
    'support': [
        'return my order', 'return order', 'return this', 'return item',
        'refund my order', 'refund order', 'get refund', 'money back',
        'refund please', 'need refund', 'want refund', 'refund request',
        'complaint', 'problem', 'issue', 'help me', 'need help',
        'contact support', 'speak to human', 'talk to human', 'human agent',
        'not working', 'damaged', 'wrong item', 'defective', 'broken',
        'cancel order', 'cancel my order', 'exchange', 'replace',
        'not received', 'missing item', 'wrong product'
    ],
    'review_view': [
        'reviews for', 'show reviews', 'see reviews', 'view reviews',
        'ratings for', 'what do people say', 'product reviews', 'customer reviews',
        'read reviews', 'check reviews', 'any reviews', 'reviews of'
    ],
    'review_submit': [
        'write review', 'write a review', 'leave review', 'leave a review',
        'submit review', 'submit a review', 'rate product', 'rate a product',
        'i want to review', 'give feedback', 'rate this', 'add review',
        'post review', 'my review', 'give review', 'review this product'
    ],
    'flash_sale': [
        'flash sale', 'deals', 'offers', 'on sale', 'special offers',
        'discounted products', 'discounted items', 'discount products',
        'what is on discount', 'sale items', 'featured products',
        'best deals', 'hot deals', 'today deals', 'offer products'
    ],
    'product_search': [
        'show products', 'show all products', 'browse products', 'all products',
        'find products', 'search products', 'looking for', 'what do you have',
        'show me products', 'display products', 'available products',
        'list products', 'product list', 'ke cha', 'k k cha',
        'details about', 'info about', 'tell me about', 'know about',
        'information about', 'show me the', 'want to know about', 'want to see'
    ],
    'categories': [
        'categories', 'category', 'types', 'kinds', 'show categories',
        'product types', 'what categories', 'all categories'
    ],
    'greeting': [
        'hi', 'hello', 'hey', 'good morning', 'good evening', 'good afternoon',
        'howdy', 'greetings', 'namaste', 'namaskar', 'hii', 'helo',
        'bro', 'yo', 'sup', 'wassup', 'man', 'dude', 'whats up', "what's up",
        'hola', 'oi', 'heyy', 'heya', 'hiya'
    ],
    'policy': [
        'shipping', 'delivery time', 'return policy', 'refund policy', 'how long',
        'payment method', 'cod', 'cash on delivery', 'delivery charge',
        'shipping charge', 'free delivery', 'delivery days'
    ],
    'thanks': [
        'thank', 'thanks', 'thank you', 'appreciated', 'dhanyabad', 'धन्यवाद'
    ],
    'bye': [
        'bye', 'goodbye', 'see you', 'later', 'exit', 'quit', 'close'
    ]
}

# Entity Patterns (Regex)
ENTITY_PATTERNS = {
    'phone_nepal': r'\b((?:98|97|96|01)\d{8})\b',
    'order_id_short': r'\b[A-Fa-f0-9]{8}\b',
    'order_uuid': r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',
    'rating': r'\b([1-5])\s*(?:star|stars|/5|out of 5)?\b',
    'quantity': r'\b(\d+)\s*(?:pieces?|items?|units?|qty|pcs?)?\b',
    'price': r'(?:rs\.?|npr\.?|रु\.?)\s*(\d+[,\d]*)',
    'email': r'[\w\.-]+@[\w\.-]+\.\w{2,}'
}

# Quick Reply Options
QUICK_REPLIES = {
    'greeting': ['Browse Products', 'Track Order', 'Flash Sales', 'Get Help'],
    'after_products': ['Buy Now', 'See Reviews', 'More Products'],
    'after_order': ['Track Order', 'Browse More', 'Get Help'],
    'after_support': ['Browse Products', 'Track Order'],
    'after_review': ['Browse Products', 'Write Another Review'],
    'confirmation': ['Yes', 'No'],
    'order_identifier': ['Use Phone Number', 'Use Order ID']
}

# Support Categories
SUPPORT_CATEGORIES = {
    'order': 'Order Related Issue',
    'product': 'Product Information',
    'complaint': 'Complaint',
    'return': 'Return/Refund Request',
    'feedback': 'Feedback',
    'general': 'General Inquiry'
}

# Response Templates
RESPONSES = {
    'greeting': "👋 Hello! Welcome to OVN Store! 🛍️\n\nHow can I help you today? You can:\n• 🔍 Browse products\n• 📦 Track orders\n• 🛒 Place orders\n• ❓ Ask me anything!\n\nJust type what you need! 😊",
    'thanks': "😊 You're welcome! Is there anything else I can help you with? 💜",
    'bye': "👋 Thank you for visiting OVN Store! Have a great day! 🌟",
    'fallback': "🤔 I'm not sure I understand. You can ask me to:\n• 🔍 Show products\n• 📦 Track orders\n• 🛒 Place an order\n• ❓ Help with any issues",
    'error': "😔 Sorry, something went wrong. Please try again.",
}
