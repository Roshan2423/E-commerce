"""
Product Handler for OVN Store Chatbot
Handles product search, browsing, and display
"""
import re
from typing import Dict, List, Optional
from pymongo import MongoClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .base import BaseHandler, HandlerResponse
from core.session import SessionData, ConversationState
from config import MONGO_URI, DATABASE_NAME


class ProductHandler(BaseHandler):
    """
    Handles all product-related queries:
    - Product search
    - Browse all products
    - Flash sales / featured
    - Categories
    - Product details
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize MongoDB connection
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DATABASE_NAME]
            self.products_col = self.db['products']
            self.categories_col = self.db['categories']
            self.db_connected = True
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            self.db_connected = False

    def can_handle(self, intent: str, state: ConversationState) -> bool:
        """Handle product-related intents when in IDLE state"""
        product_intents = ['product_search', 'flash_sale', 'categories', 'product_detail']
        return intent in product_intents and state == ConversationState.IDLE

    def handle(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process product queries"""
        intent = entities.get('intent', 'product_search')

        if intent == 'flash_sale':
            return self.handle_flash_sale(session)
        elif intent == 'categories':
            return self.handle_categories(session)
        elif intent == 'product_detail':
            return self.handle_product_detail(message, session)
        else:
            return self.handle_search(message, session, entities)

    def handle_search(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Handle product search"""
        max_price = entities.get('max_price')
        products = self.search_products(message, max_price=max_price)

        # Store in session for later reference
        session.last_viewed_products = products

        if products:
            return self.response(
                f"Here are {len(products)} product{'s' if len(products) > 1 else ''} I found for you!",
                products=products,
                quick_replies=['Buy Now', 'See More', 'Track Order']
            )
        else:
            return self.response(
                "I couldn't find products matching your search. Try different keywords or browse all products!",
                quick_replies=['Show All Products', 'Flash Sales', 'Categories']
            )

    def handle_flash_sale(self, session: SessionData) -> HandlerResponse:
        """Handle flash sale / featured products request"""
        products = self.get_featured_products(limit=8)

        if products:
            return self.response(
                f"🔥 Check out our {len(products)} amazing deals! Limited time offers.",
                products=products,
                quick_replies=['Buy Now', 'Show All', 'Track Order']
            )
        else:
            return self.response(
                "No flash sales right now. Check out our regular products!",
                quick_replies=['Show All Products', 'Categories']
            )

    def handle_categories(self, session: SessionData) -> HandlerResponse:
        """Handle category listing request"""
        categories = self.get_all_categories()

        if categories:
            return self.response(
                f"We have products in these categories: **{', '.join(categories)}**\n\nJust tell me which category interests you!",
                categories=categories,
                quick_replies=categories[:4]  # First 4 categories as quick replies
            )
        else:
            return self.response(
                "Categories are being updated. Try browsing all products!",
                quick_replies=['Show All Products', 'Flash Sales']
            )

    def handle_product_detail(self, message: str, session: SessionData) -> HandlerResponse:
        """Handle specific product detail request"""
        product = self.get_product_detail(message)

        if product:
            formatted = self.format_product(product)
            session.last_viewed_products = [formatted]

            # Build detailed response
            name = formatted.get('name', '')
            desc = formatted.get('description', '')[:200]
            price = formatted.get('price', 0)
            compare = formatted.get('compare_price', 0)
            stock = formatted.get('stock', 0)
            category = formatted.get('category', '')
            rating = formatted.get('rating', 0)
            review_count = formatted.get('review_count', 0)

            response_text = f"**{name}**\n\n"
            if desc:
                response_text += f"{desc}...\n\n"
            response_text += f"**Price:** {self.format_price(price)}"
            if compare and compare > price:
                response_text += f" ~~{self.format_price(compare)}~~"
            response_text += f"\n**Category:** {category}"
            response_text += f"\n**Stock:** {'In Stock ✅' if stock > 0 else 'Out of Stock ❌'}"
            if rating > 0:
                stars = '★' * int(rating) + '☆' * (5 - int(rating))
                response_text += f"\n**Rating:** {stars} ({rating}/5 - {review_count} reviews)"
            response_text += f"\n\nClick the product card below to buy!"

            return self.response(
                response_text,
                products=[formatted],
                quick_replies=['Buy This', 'See Reviews', 'More Products']
            )
        else:
            return self.response(
                "I couldn't find that specific product. Try searching with different keywords!",
                quick_replies=['Show All Products', 'Flash Sales']
            )

    # ==================== MongoDB Methods ====================

    def format_product(self, product: Dict) -> Dict:
        """Format a MongoDB product document"""
        regular_price = float(product.get("price", 0))
        special_price = float(product.get("compare_price")) if product.get("compare_price") else None
        flash_price = float(product.get("flash_sale_price")) if product.get("flash_sale_price") else None
        is_flash_sale = product.get("is_flash_sale", False)

        # Determine display price
        if flash_price:
            display_price = flash_price
            original_price = special_price if special_price else regular_price
        elif special_price:
            display_price = special_price
            original_price = regular_price
        else:
            display_price = regular_price
            original_price = 0

        return {
            "id": product.get("django_id", ""),
            "name": product.get("name", ""),
            "price": display_price,
            "compare_price": original_price,
            "flash_sale_price": flash_price,
            "image": product.get("main_image", ""),
            "category": product.get("category_name", "General"),
            "stock": product.get("stock_quantity", 0),
            "rating": product.get("avg_rating", 0),
            "review_count": product.get("review_count", 0),
            "is_featured": product.get("is_featured", False),
            "is_flash_sale": is_flash_sale,
            "description": (product.get("description", "") or "")[:100]
        }

    def get_all_products(self, limit: int = 20) -> List[Dict]:
        """Get all active products"""
        if not self.db_connected:
            return []
        try:
            products = self.products_col.find({"is_active": True}).limit(limit)
            return [self.format_product(p) for p in products]
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_featured_products(self, limit: int = 10) -> List[Dict]:
        """Get featured/flash sale products"""
        if not self.db_connected:
            return []
        try:
            products = self.products_col.find({
                "is_active": True,
                "$or": [{"is_featured": True}, {"is_flash_sale": True}]
            }).limit(limit)
            return [self.format_product(p) for p in products]
        except Exception as e:
            print(f"Error: {e}")
            return []

    def search_products(self, query: str, max_price: float = None, limit: int = 10) -> List[Dict]:
        """Search products by name or description with fuzzy matching"""
        if not self.db_connected:
            return []
        try:
            # First try exact/near-exact name match (for when user pastes full product name)
            exact_match = self.products_col.find_one({
                "is_active": True,
                "name": {"$regex": f"^{re.escape(query[:50])}.*", "$options": "i"}
            })
            if exact_match:
                return [self.format_product(exact_match)]

            # Extract keywords - preserve numbers and units together
            query_clean = query.lower()
            # Handle patterns like "220clover" -> "220 clover" or "220ml" -> "220 ml"
            query_clean = re.sub(r'(\d+)(ml|l|g|kg|oz|cm|mm|inch)', r'\1 \2', query_clean)
            query_clean = re.sub(r'(\d+)([a-zA-Z])', r'\1 \2', query_clean)

            keywords = re.findall(r'\b\w+\b', query_clean)
            stop_words = {'show', 'me', 'the', 'a', 'an', 'i', 'want', 'need', 'find', 'search',
                         'looking', 'for', 'can', 'you', 'please', 'what', 'do', 'have', 'products',
                         'product', 'all', 'everything', 'browse', 'see', 'buy', 'get', 'order',
                         'to', 'it', 'this', 'that', 'is', 'are', 'and', 'or',
                         'details', 'about', 'know', 'info', 'information', 'tell', 'give',
                         'th', 'of', 'more', 'some', 'any'}
            keywords = [k for k in keywords if k not in stop_words and len(k) > 1]

            if not keywords:
                return self.get_all_products(limit)

            # Build query with flexible matching
            regex_patterns = []
            for keyword in keywords:
                # Create flexible regex that handles variations
                # "clover" matches "clover", "220clover" matches "220.*clover" or "220 ml clover"
                flex_pattern = f".*{re.escape(keyword)}.*"
                regex_patterns.append({"name": {"$regex": flex_pattern, "$options": "i"}})
                regex_patterns.append({"description": {"$regex": flex_pattern, "$options": "i"}})
                regex_patterns.append({"category_name": {"$regex": flex_pattern, "$options": "i"}})

            query_filter = {"is_active": True, "$or": regex_patterns}

            if max_price:
                query_filter["price"] = {"$lte": max_price}

            products = list(self.products_col.find(query_filter).limit(limit * 2))

            # Score and rank products by relevance
            scored_products = []
            for p in products:
                score = 0
                name_lower = p.get('name', '').lower()
                # Exact keyword matches in name get higher score
                for kw in keywords:
                    if kw in name_lower:
                        score += 10
                    if name_lower.startswith(kw):
                        score += 5
                # Number matches (like "220") get bonus
                for kw in keywords:
                    if kw.isdigit() and kw in name_lower:
                        score += 15
                scored_products.append((score, p))

            # Sort by score descending
            scored_products.sort(key=lambda x: x[0], reverse=True)
            return [self.format_product(p) for _, p in scored_products[:limit]]
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_products_by_category(self, category_name: str, limit: int = 10) -> List[Dict]:
        """Get products by category"""
        if not self.db_connected:
            return []
        try:
            products = self.products_col.find({
                "is_active": True,
                "category_name": {"$regex": category_name, "$options": "i"}
            }).limit(limit)
            return [self.format_product(p) for p in products]
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_all_categories(self) -> List[str]:
        """Get all category names"""
        if not self.db_connected:
            return []
        try:
            categories = self.categories_col.find({}, {"name": 1})
            return [cat["name"] for cat in categories]
        except:
            return []

    def get_product_detail(self, query: str) -> Optional[Dict]:
        """Get detailed info about a specific product"""
        if not self.db_connected:
            return None
        try:
            keywords = re.findall(r'\b\w+\b', query.lower())
            stop_words = {'tell', 'me', 'more', 'about', 'the', 'a', 'an', 'what', 'is',
                         'details', 'detail', 'info', 'information', 'describe', 'show'}
            keywords = [k for k in keywords if k not in stop_words and len(k) > 2]

            if not keywords:
                return None

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

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get product by Django ID"""
        if not self.db_connected:
            return None
        try:
            product = self.products_col.find_one({"django_id": product_id, "is_active": True})
            return self.format_product(product) if product else None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def find_product_by_name(self, name: str) -> Optional[Dict]:
        """Find a product by partial name match with fuzzy support"""
        if not self.db_connected:
            return None
        try:
            # Clean the name - handle patterns like "220clover" -> "220 clover"
            name_clean = name.lower()
            name_clean = re.sub(r'(\d+)(ml|l|g|kg|oz|cm|mm|inch)', r'\1 \2', name_clean)
            name_clean = re.sub(r'(\d+)([a-zA-Z])', r'\1 \2', name_clean)

            # First try exact match
            product = self.products_col.find_one({
                "is_active": True,
                "name": {"$regex": f"^{re.escape(name[:30])}.*", "$options": "i"}
            })
            if product:
                return self.format_product(product)

            # Try with cleaned keywords
            keywords = re.findall(r'\b\w+\b', name_clean)
            keywords = [k for k in keywords if len(k) > 1]

            if keywords:
                # Build regex pattern that matches all keywords in any order
                patterns = [{"name": {"$regex": kw, "$options": "i"}} for kw in keywords]
                product = self.products_col.find_one({
                    "is_active": True,
                    "$and": patterns
                })
                if product:
                    return self.format_product(product)

                # Try with $or for partial matches
                product = self.products_col.find_one({
                    "is_active": True,
                    "$or": patterns
                })
                if product:
                    return self.format_product(product)

            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
