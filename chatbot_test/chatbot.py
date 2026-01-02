"""
OVN Store Intelligent Chatbot
Uses Groq API (FREE) with Llama 3.1 for smart responses
Connects to MongoDB database for real product/order data
"""

import re
import os
from pymongo import MongoClient
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ovn_store")

# Groq API Configuration (get from environment variable)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


class OVNStoreChatbot:
    def __init__(self):
        # Initialize MongoDB client
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DATABASE_NAME]
            self.products_col = self.db['products']
            self.categories_col = self.db['categories']
            self.db_connected = True
            print("Connected to MongoDB successfully!")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            self.db_connected = False

        # Initialize Groq client
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.conversation_history = []

        # System prompt
        self.system_prompt = """You are OVN Store's friendly AI shopping assistant.

IMPORTANT: Look at the "Products found" count in the context.
- If products found > 0: Say "Here are the products I found!" or similar welcoming message
- If products found = 0: Say "Sorry, I couldn't find products matching your search. Try browsing all products!"

STORE INFO:
- Free shipping on orders above Rs. 1000
- 7-day return policy
- Cash on Delivery available
- Delivery: 3-5 business days in Nepal

Keep responses brief (1-2 sentences). Product cards with images appear automatically below your message.
"""

    def format_product(self, product):
        """Format a MongoDB product document - matches Django API logic"""
        # Get prices
        regular_price = float(product.get("price", 0))
        special_price = float(product.get("compare_price")) if product.get("compare_price") else None
        flash_price = float(product.get("flash_sale_price")) if product.get("flash_sale_price") else None
        is_flash_sale = product.get("is_flash_sale", False)

        # Determine display price and compare price (matches api_views.py logic)
        if flash_price:
            # Flash sale with flash_sale_price: show flash price, strikethrough special or regular
            display_price = flash_price
            original_price = special_price if special_price else regular_price
        elif special_price:
            # Has special/compare price: show special price, strikethrough regular
            display_price = special_price
            original_price = regular_price
        else:
            # Just regular price
            display_price = regular_price
            original_price = 0

        return {
            "id": product.get("django_id", ""),  # Use Django ID for frontend URLs
            "name": product.get("name", ""),
            "price": display_price,  # Display price (flash/special/regular)
            "compare_price": original_price,  # Original price for strikethrough
            "flash_sale_price": flash_price,
            "image": product.get("main_image", ""),
            "category": product.get("category_name", "General"),
            "stock": product.get("stock_quantity", 0),
            "rating": product.get("avg_rating", 0),  # Average rating from reviews
            "review_count": product.get("review_count", 0),
            "is_featured": product.get("is_featured", False),
            "is_flash_sale": is_flash_sale,
            "description": (product.get("description", "") or "")[:100]
        }

    def get_all_products(self, limit=20):
        """Get all active products"""
        try:
            products = self.products_col.find({"is_active": True}).limit(limit)
            return [self.format_product(p) for p in products]
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_featured_products(self, limit=10):
        """Get featured products"""
        try:
            products = self.products_col.find({
                "is_active": True,
                "$or": [{"is_featured": True}, {"is_flash_sale": True}]
            }).limit(limit)
            return [self.format_product(p) for p in products]
        except Exception as e:
            print(f"Error: {e}")
            return []

    def search_products(self, query, max_price=None, limit=10):
        """Search products by name or description"""
        try:
            # Extract keywords
            keywords = re.findall(r'\b\w+\b', query.lower())
            stop_words = {'show', 'me', 'the', 'a', 'an', 'i', 'want', 'need', 'find', 'search',
                         'looking', 'for', 'can', 'you', 'please', 'what', 'do', 'have', 'products',
                         'product', 'all', 'everything', 'browse', 'see'}
            keywords = [k for k in keywords if k not in stop_words and len(k) > 2]

            if not keywords:
                return self.get_all_products(limit)

            # Build regex pattern for search
            regex_patterns = []
            for keyword in keywords:
                regex_patterns.append({"name": {"$regex": keyword, "$options": "i"}})
                regex_patterns.append({"description": {"$regex": keyword, "$options": "i"}})

            query_filter = {"is_active": True, "$or": regex_patterns}

            if max_price:
                query_filter["price"] = {"$lte": max_price}

            products = self.products_col.find(query_filter).limit(limit)
            return [self.format_product(p) for p in products]
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_all_categories(self):
        """Get all category names"""
        try:
            categories = self.categories_col.find({}, {"name": 1})
            return [cat["name"] for cat in categories]
        except:
            return []

    def get_products_by_category(self, category_name, limit=10):
        """Get products by category"""
        try:
            products = self.products_col.find({
                "is_active": True,
                "category_name": {"$regex": category_name, "$options": "i"}
            }).limit(limit)
            return [self.format_product(p) for p in products]
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_product_stats(self):
        """Get store statistics"""
        try:
            return {
                "total_products": self.products_col.count_documents({"is_active": True}),
                "categories": self.get_all_categories(),
                "featured_count": self.products_col.count_documents({"is_active": True, "is_featured": True})
            }
        except:
            return {}

    def get_product_detail(self, query):
        """Get detailed info about a specific product"""
        try:
            # Extract keywords from query
            keywords = re.findall(r'\b\w+\b', query.lower())
            stop_words = {'tell', 'me', 'more', 'about', 'the', 'a', 'an', 'what', 'is',
                         'details', 'detail', 'info', 'information', 'describe', 'show'}
            keywords = [k for k in keywords if k not in stop_words and len(k) > 2]

            if not keywords:
                return None

            # Search for product matching keywords
            for keyword in keywords:
                product = self.products_col.find_one({
                    "is_active": True,
                    "$or": [
                        {"name": {"$regex": keyword, "$options": "i"}},
                        {"description": {"$regex": keyword, "$options": "i"}}
                    ]
                })
                if product:
                    return product
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def detect_intent_and_get_products(self, user_message):
        """Detect user intent and fetch relevant products"""
        message_lower = user_message.lower()
        products = []
        intent = "general"
        product_detail = None

        # Product detail request (tell me more about, what is, details about)
        if any(phrase in message_lower for phrase in ["tell me more", "tell me about", "more about", "details about", "what is the", "describe"]):
            product_detail = self.get_product_detail(user_message)
            if product_detail:
                products = [self.format_product(product_detail)]
                intent = "product_detail"
                return intent, products, product_detail

        # Flash sale / deals / featured
        if any(word in message_lower for word in ["flash", "sale", "deal", "offer", "discount", "featured", "special"]):
            products = self.get_featured_products(limit=8)
            intent = "featured"

        # Category query
        elif "category" in message_lower or "categories" in message_lower:
            intent = "categories"

        # Product search
        elif any(word in message_lower for word in ["show", "find", "search", "looking", "want", "need", "buy", "product", "all"]):
            price_match = re.search(r'(?:under|below|less than|max|budget)\s*(?:rs\.?|npr\.?)?\s*(\d+[,\d]*)', message_lower)
            max_price = int(price_match.group(1).replace(",", "")) if price_match else None
            products = self.search_products(user_message, max_price=max_price, limit=8)
            intent = "search"

        # Greetings
        elif any(word in message_lower for word in ["hi", "hello", "hey", "good morning", "good evening"]):
            intent = "greeting"

        # Help/policy
        elif any(word in message_lower for word in ["return", "shipping", "delivery", "policy", "help", "how"]):
            intent = "help"

        # Default - show all products
        else:
            products = self.get_all_products(limit=6)
            intent = "browse"

        return intent, products, None

    def generate_response(self, intent, products, categories, user_message, product_detail=None):
        """Generate appropriate response based on intent and results"""
        product_count = len(products)

        if intent == "product_detail" and products and len(products) > 0:
            # Use formatted product data (with correct pricing)
            p = products[0]
            name = p.get("name", "")
            desc = p.get("description", "")
            price = p.get("price", 0)
            compare = p.get("compare_price", 0)
            stock = p.get("stock", 0)
            category = p.get("category", "")
            rating = p.get("rating", 0)
            review_count = p.get("review_count", 0)

            response = f"**{name}**\n\n"
            if desc:
                response += f"{desc}...\n\n"
            response += f"**Price:** Rs. {price:,.0f}"
            if compare and compare > price:
                response += f" ~~Rs. {compare:,.0f}~~"
            response += f"\n**Category:** {category}"
            response += f"\n**Stock:** {'In Stock' if stock > 0 else 'Out of Stock'}"
            if rating > 0:
                response += f"\n**Rating:** {'★' * int(rating)}{'☆' * (5-int(rating))} ({rating}/5 - {review_count} reviews)"
            response += f"\n\nClick the product card below to buy now!"
            return response

        if intent == "greeting":
            return "Hello! Welcome to OVN Store. How can I help you today? You can browse products, check deals, or ask about our policies!"

        elif intent == "categories":
            if categories:
                return f"We have products in these categories: **{', '.join(categories)}**. Click on any category to explore!"
            return "We're currently updating our categories. Please browse all products!"

        elif intent == "featured":
            if product_count > 0:
                return f"Here are our {product_count} featured product{'s' if product_count > 1 else ''}! Great deals just for you."
            return "No featured products right now. Check out our regular products below!"

        elif intent == "search" or intent == "browse":
            if product_count > 0:
                return f"Here are {product_count} product{'s' if product_count > 1 else ''} I found for you! Click any product to view details."
            return "I couldn't find products matching your search. Try browsing all products or searching with different keywords!"

        elif intent == "help":
            return """**Store Policies:**
* Free shipping on orders above Rs. 1,000
* 7-day return policy for unused items
* Cash on Delivery available
* Delivery: 3-5 business days in Nepal

How else can I help you?"""

        else:
            if product_count > 0:
                return f"Here are {product_count} product{'s' if product_count > 1 else ''} you might like!"
            return "How can I help you today? Try asking about products, deals, or our store policies!"

    def chat(self, user_message, user_info=None):
        """Main chat function"""
        intent, products, product_detail = self.detect_intent_and_get_products(user_message)
        categories = self.get_all_categories()

        # Generate smart response
        ai_message = self.generate_response(intent, products, categories, user_message, product_detail)

        # Store in history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": ai_message})
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

        return {
            "message": ai_message,
            "products": products,
            "categories": categories if intent == "categories" else [],
            "intent": intent
        }

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        return "Conversation history cleared!"


if __name__ == "__main__":
    bot = OVNStoreChatbot()
    print("\nTesting chatbot...")
    result = bot.chat("Show me all products")
    print(f"Message: {result['message']}")
    print(f"Products found: {len(result['products'])}")
    for p in result['products'][:3]:
        print(f"  - {p['name'][:40]}: Rs. {p['price']}, Image: {p['image'][:50] if p['image'] else 'None'}...")
