"""
Order Placement Handler for OVN Store Chatbot
Handles placing orders through conversation with improved flow
"""
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .base import BaseHandler, HandlerResponse
from .product import ProductHandler
from core.session import SessionData, ConversationState

# Import delivery rates
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend', 'orders'))
try:
    from delivery_rates import DELIVERY_RATES, get_districts, get_rate_by_location
except ImportError:
    DELIVERY_RATES = []
    def get_districts():
        return []
    def get_rate_by_location(loc):
        return 100


class OrderPlacementHandler(BaseHandler):
    """
    Handles complete order placement flow:
    1. Ask for product name if not specified
    2. Show product and ask if it's correct
    3. If not, show related products
    4. Ask: details or buy?
    5. Collect delivery info with location-based rates
    6. Create order and show confirmation
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_handler = ProductHandler()

    def can_handle(self, intent: str, state: ConversationState) -> bool:
        """Handle order placement intent or active placement states"""
        if intent == 'order_placement' and state == ConversationState.IDLE:
            return True
        placement_states = [
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
            ConversationState.ORDER_PLACEMENT_CONFIRMING
        ]
        return state in placement_states

    def handle(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process order placement step"""
        state = session.state

        # Initial request
        if state == ConversationState.IDLE:
            return self.start_order(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_ASKING_PRODUCT:
            return self.process_product_name(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT:
            return self.process_product_selection(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT:
            return self.process_product_confirmation(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_ASKING_ACTION:
            return self.process_action_choice(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_SHOWING_DETAILS:
            return self.process_after_details(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_AWAITING_QUANTITY:
            return self.process_quantity(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_AWAITING_NAME:
            return self.process_name(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_AWAITING_PHONE:
            return self.process_phone(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_SELECTING_DISTRICT:
            return self.process_district_selection(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_SELECTING_LOCATION:
            return self.process_location_selection(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK:
            return self.process_landmark(message, session, entities)

        elif state == ConversationState.ORDER_PLACEMENT_CONFIRMING:
            return self.process_confirmation(message, session, entities)

        return self.start_order(message, session, entities)

    def start_order(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Start order placement - check if product is specified"""
        msg_lower = message.lower()

        # Check if user is saying "yes" to buy a recently mentioned product
        buy_confirmation_words = ['yes', 'yeah', 'yep', 'ok', 'okay', 'sure', 'buy it', 'order it', 'want it', 'take it']
        is_buy_confirmation = any(word in msg_lower for word in buy_confirmation_words)

        # If user confirms buying and we have recently viewed products, use the first one
        if is_buy_confirmation and session.last_viewed_products:
            product = session.last_viewed_products[0]
            session.set_context('selected_product', product)
            session.set_state(ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT)
            return self.response(
                f"👍 You want to order:\n\n{self.format_product_card(product)}\n\n"
                f"Is this correct? 🤔",
                products=[product],
                next_state=ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT
            )

        # Try to find product from message
        keywords = entities.get('product_keywords', [])
        if not keywords:
            from core.intent import EntityExtractor
            extractor = EntityExtractor()
            keywords = extractor.extract_product_keywords(message)

        if keywords:
            # User mentioned a product, search for it
            return self.search_and_show_product(' '.join(keywords), session)

        # Check if we have recently viewed products to suggest
        if session.last_viewed_products:
            products = session.last_viewed_products[:4]
            session.set_context('product_options', products)
            session.set_state(ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT)
            return self.response(
                "🛒 Which product would you like to order?\n\n"
                "Here are some products you recently viewed:",
                products=products,
                next_state=ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT
            )

        # No product specified - ask for product name
        session.set_state(ConversationState.ORDER_PLACEMENT_ASKING_PRODUCT)
        return self.response(
            "🛒 I'd love to help you place an order!\n\n"
            "What product would you like to order? Please tell me the name of the product. 🔍",
            next_state=ConversationState.ORDER_PLACEMENT_ASKING_PRODUCT
        )

    def process_product_name(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """User provided product name"""
        return self.search_and_show_product(message.strip(), session)

    def search_and_show_product(self, query: str, session: SessionData) -> HandlerResponse:
        """Search for product and show results"""
        products = self.product_handler.search_products(query, limit=5)

        if len(products) == 1:
            # Found exactly one product - show it and ask if correct
            session.set_context('selected_product', products[0])
            session.set_state(ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT)
            return self.response(
                f"✨ I found this product:\n\n{self.format_product_card(products[0])}\n\n"
                f"Is this what you're looking for? 🤔",
                products=products,
                next_state=ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT
            )

        elif len(products) > 1:
            # Multiple products found
            session.set_context('product_options', products)
            session.set_state(ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT)

            product_list = "\n".join([f"**{i+1}.** {p['name'][:50]}" for i, p in enumerate(products)])

            return self.response(
                f"🔍 I found {len(products)} products matching '{query}':\n\n"
                f"{product_list}\n\n"
                f"👆 Please type a number (1-{len(products)}) to select, or click on a product.",
                products=products,
                next_state=ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT
            )

        # No products found
        session.set_state(ConversationState.ORDER_PLACEMENT_ASKING_PRODUCT)
        return self.response(
            f"😕 Sorry, I couldn't find any products matching '{query}'.\n\n"
            f"Please try a different product name or describe what you're looking for. 🔍",
            next_state=ConversationState.ORDER_PLACEMENT_ASKING_PRODUCT
        )

    def process_product_selection(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """User selecting from multiple products"""
        products = session.get_context('product_options', [])
        msg_lower = message.lower().strip()

        # Check for number selection
        try:
            # Extract number from message (handles "1", "#1", "product 1", etc.)
            digits = ''.join(filter(str.isdigit, message))
            if digits:
                selection = int(digits)
                if 1 <= selection <= len(products):
                    product = products[selection - 1]
                    session.set_context('selected_product', product)
                    session.set_state(ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT)
                    return self.response(
                        f"👍 You selected:\n\n{self.format_product_card(product)}\n\n"
                        f"Is this the product you want? 🤔",
                        products=[product],
                        next_state=ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT
                    )
        except ValueError:
            pass

        # If user says "yes" or "first", select the first product
        if self.is_confirmation(msg_lower) or msg_lower in ['first', 'top', 'top one']:
            if products:
                product = products[0]
                session.set_context('selected_product', product)
                session.set_state(ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT)
                return self.response(
                    f"👍 You selected:\n\n{self.format_product_card(product)}\n\n"
                    f"Is this the product you want? 🤔",
                    products=[product],
                    next_state=ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT
                )

        # Check if message matches any product name
        for i, product in enumerate(products):
            if msg_lower in product.get('name', '').lower():
                session.set_context('selected_product', product)
                session.set_state(ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT)
                return self.response(
                    f"👍 You selected:\n\n{self.format_product_card(product)}\n\n"
                    f"Is this the product you want? 🤔",
                    products=[product],
                    next_state=ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT
                )

        # User might have typed product name - search again
        return self.search_and_show_product(message.strip(), session)

    def process_product_confirmation(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """User confirming if this is the right product"""
        if self.is_confirmation(message):
            # Yes, this is the right product
            product = session.get_context('selected_product', {})
            session.set_state(ConversationState.ORDER_PLACEMENT_ASKING_ACTION)
            return self.response(
                f"🎉 Great! I can help you with **{product.get('name', 'this product')[:40]}**.\n\n"
                f"What would you like to do?\n"
                f"1️⃣ **See more details** about this product\n"
                f"2️⃣ **Buy it now** - I'll help you place an order\n\n"
                f"Just type '1' for details or '2' to buy. 👇",
                products=[product],
                next_state=ConversationState.ORDER_PLACEMENT_ASKING_ACTION
            )

        if self.is_rejection(message):
            # Not the right product - show alternatives
            products = self.product_handler.get_all_products(limit=8)
            session.set_context('product_options', products)
            session.set_state(ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT)

            product_list = "\n".join([f"**{i+1}.** {p['name'][:50]}" for i, p in enumerate(products)])

            return self.response(
                f"👌 No problem! Here are some other products:\n\n"
                f"{product_list}\n\n"
                f"👆 Click on a product or type its number to select it.\n"
                f"Or tell me what product you're looking for. 🔍",
                products=products,
                next_state=ConversationState.ORDER_PLACEMENT_SELECTING_PRODUCT
            )

        return self.response(
            "🤔 Is this the product you're looking for? (Yes/No)",
            next_state=ConversationState.ORDER_PLACEMENT_CONFIRMING_PRODUCT
        )

    def process_action_choice(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """User choosing between details or buy"""
        message_lower = message.lower().strip()
        product = session.get_context('selected_product', {})

        # Check for buy/order intent
        if '2' in message or 'buy' in message_lower or 'order' in message_lower or 'yes' in message_lower:
            return self.start_checkout(session)

        # Check for details intent
        if '1' in message or 'detail' in message_lower or 'more' in message_lower:
            session.set_state(ConversationState.ORDER_PLACEMENT_SHOWING_DETAILS)
            return self.response(
                self.format_product_details(product) +
                "\n\n🛒 Would you like to order this product?",
                products=[product],
                next_state=ConversationState.ORDER_PLACEMENT_SHOWING_DETAILS
            )

        return self.response(
            "👇 Please choose:\n"
            "1️⃣ See more details\n"
            "2️⃣ Buy now\n\n"
            "Type 1 or 2",
            next_state=ConversationState.ORDER_PLACEMENT_ASKING_ACTION
        )

    def process_after_details(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """After showing details, user decides to buy or not"""
        if self.is_confirmation(message) or 'buy' in message.lower() or 'order' in message.lower() or 'yes' in message.lower():
            return self.start_checkout(session)

        if self.is_rejection(message):
            session.reset_state()
            return self.response(
                "👌 No problem! Is there anything else I can help you with? 😊",
                reset_state=True
            )

        return self.response(
            "🛒 Would you like to order this product? (Yes/No)",
            next_state=ConversationState.ORDER_PLACEMENT_SHOWING_DETAILS
        )

    def start_checkout(self, session: SessionData) -> HandlerResponse:
        """Start the checkout process"""
        product = session.get_context('selected_product', {})

        # Ask for quantity
        session.set_state(ConversationState.ORDER_PLACEMENT_AWAITING_QUANTITY)
        return self.response(
            f"🛍️ Let's place your order for **{product.get('name', 'this product')[:40]}**!\n\n"
            f"💰 **Price:** {self.format_price(product.get('price', 0))}\n\n"
            f"How many would you like to order? 🔢",
            products=[product],
            next_state=ConversationState.ORDER_PLACEMENT_AWAITING_QUANTITY
        )

    def process_quantity(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process quantity input"""
        # Extract quantity
        quantity = 1
        try:
            quantity = int(message.strip())
        except ValueError:
            # Try to extract number from text
            digits = ''.join(filter(str.isdigit, message))
            if digits:
                quantity = int(digits)

        if quantity < 1:
            quantity = 1
        if quantity > 10:
            return self.response(
                "⚠️ Maximum quantity is 10 per order. Please enter a quantity between 1-10.",
                next_state=ConversationState.ORDER_PLACEMENT_AWAITING_QUANTITY
            )

        session.set_context('quantity', quantity)
        product = session.get_context('selected_product', {})
        item_total = product.get('price', 0) * quantity

        # Ask for name
        session.set_state(ConversationState.ORDER_PLACEMENT_AWAITING_NAME)

        if session.user_name:
            return self.response(
                f"✅ **Quantity:** {quantity} (Subtotal: {self.format_price(item_total)})\n\n"
                f"👤 I have your name as **{session.user_name}**.\n"
                f"Should I use this name for delivery?",
                next_state=ConversationState.ORDER_PLACEMENT_AWAITING_NAME
            )

        return self.response(
            f"✅ **Quantity:** {quantity} (Subtotal: {self.format_price(item_total)})\n\n"
            f"👤 Please enter your **full name** for delivery:",
            next_state=ConversationState.ORDER_PLACEMENT_AWAITING_NAME
        )

    def process_name(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process customer name"""
        if self.is_confirmation(message) and session.user_name:
            session.set_context('customer_name', session.user_name)
        else:
            name = message.strip()
            if len(name) < 2:
                return self.response(
                    "⚠️ Please enter a valid name for delivery.",
                    next_state=ConversationState.ORDER_PLACEMENT_AWAITING_NAME
                )
            session.set_context('customer_name', name)
            session.remember_user_info(name=name)

        # Ask for phone
        session.set_state(ConversationState.ORDER_PLACEMENT_AWAITING_PHONE)

        if session.user_phone:
            return self.response(
                f"📱 Should I use phone number **{session.user_phone}**?",
                next_state=ConversationState.ORDER_PLACEMENT_AWAITING_PHONE
            )

        return self.response(
            "📱 Please enter your **10-digit mobile number**:",
            next_state=ConversationState.ORDER_PLACEMENT_AWAITING_PHONE
        )

    def process_phone(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process phone number"""
        if self.is_confirmation(message) and session.user_phone:
            session.set_context('contact_number', session.user_phone)
        else:
            phone = entities.get('phone')
            if not phone:
                digits = ''.join(filter(str.isdigit, message))
                if len(digits) == 10:
                    phone = digits

            if not phone or len(phone) != 10:
                return self.response(
                    "⚠️ Please enter a valid 10-digit mobile number.",
                    next_state=ConversationState.ORDER_PLACEMENT_AWAITING_PHONE
                )

            session.set_context('contact_number', phone)
            session.remember_user_info(phone=phone)

        # Show district selection for delivery
        return self.show_district_selection(session)

    def show_district_selection(self, session: SessionData) -> HandlerResponse:
        """Show available districts for delivery"""
        districts = get_districts()

        if not districts:
            # Fallback if no districts loaded
            session.set_state(ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK)
            return self.response(
                "📍 Please enter your **delivery address** (District, City/Area):",
                next_state=ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK
            )

        # Get first 20 popular districts
        popular_districts = ['Kathmandu', 'Lalitpur', 'Bhaktapur', 'Chitwan', 'Kaski', 'Morang', 'Jhapa', 'Rupandehi', 'Sunsari', 'Parsa']
        available_popular = [d for d in popular_districts if d in districts]

        session.set_context('available_districts', districts)
        session.set_state(ConversationState.ORDER_PLACEMENT_SELECTING_DISTRICT)

        district_list = "\n".join([f"📍 {d}" for d in available_popular[:10]])

        return self.response(
            f"🗺️ **Select your district for delivery:**\n\n"
            f"Popular districts:\n{district_list}\n\n"
            f"👆 Type your district name (e.g., 'Kathmandu', 'Chitwan').\n"
            f"🚚 We deliver to all 77 districts of Nepal!",
            next_state=ConversationState.ORDER_PLACEMENT_SELECTING_DISTRICT
        )

    def process_district_selection(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process district selection"""
        districts = session.get_context('available_districts', get_districts())
        user_input = message.strip()
        msg_lower = message.lower().strip()

        # Check if user is trying to restart/change intent (not entering a location)
        restart_keywords = ['order', 'buy', 'want to', 'search', 'find', 'show', 'cancel', 'stop', 'exit', 'back', 'start over']
        if any(keyword in msg_lower for keyword in restart_keywords) and not any(loc['location'].lower() in msg_lower for loc in DELIVERY_RATES):
            # User wants to restart - clear and go back to start
            session.set_state(ConversationState.IDLE)
            return self.start_order(message, session, entities)

        # Extract location from sentences like "i live in hetauda", "but i live in hetauda"
        import re
        location_patterns = [
            r'(?:i\s+)?(?:live|stay|am)\s+(?:in|at|from)\s+(\w+)',  # "i live in hetauda", "live in kathmandu"
            r'(?:from|in|at)\s+(\w+)',  # "from hetauda", "in kathmandu"
            r'^(\w+)$',  # Just the location name
        ]

        extracted_location = None
        for pattern in location_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                extracted_location = match.group(1).title()
                break

        if not extracted_location:
            extracted_location = user_input.title()

        # First, try to find matching district by name
        matching_district = None
        for district in districts:
            if district.lower() == extracted_location.lower() or district.lower() in extracted_location.lower():
                matching_district = district
                break

        if not matching_district:
            # Try partial match on district
            for district in districts:
                if extracted_location.lower() in district.lower():
                    matching_district = district
                    break

        # If no district match, check if user entered a LOCATION name (like Hetauda, Bharatpur)
        if not matching_district:
            for item in DELIVERY_RATES:
                if item['location'].lower() == extracted_location.lower():
                    # Found the location - use its district and skip to location selection
                    matching_district = item['district']
                    session.set_context('selected_district', matching_district)
                    session.set_context('selected_location', item['location'])
                    session.set_context('delivery_charge', item['rate'])
                    session.set_state(ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK)
                    return self.response(
                        f"📍 **Location:** {item['location']}, {matching_district}\n"
                        f"🚚 **Delivery Charge:** Rs. {item['rate']}\n\n"
                        f"🏠 Please enter any **landmark** near your delivery address\n"
                        f"(or type 'skip' if none):",
                        next_state=ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK
                    )

            # Try partial match on location names
            for item in DELIVERY_RATES:
                if extracted_location.lower() in item['location'].lower():
                    matching_district = item['district']
                    session.set_context('selected_district', matching_district)
                    session.set_context('selected_location', item['location'])
                    session.set_context('delivery_charge', item['rate'])
                    session.set_state(ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK)
                    return self.response(
                        f"📍 **Location:** {item['location']}, {matching_district}\n"
                        f"🚚 **Delivery Charge:** Rs. {item['rate']}\n\n"
                        f"🏠 Please enter any **landmark** near your delivery address\n"
                        f"(or type 'skip' if none):",
                        next_state=ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK
                    )

        if not matching_district:
            return self.response(
                f"⚠️ Location '{extracted_location}' not found. Please enter a valid district or city name.\n\n"
                f"Examples: Kathmandu, Lalitpur, Chitwan, Hetauda, Bharatpur, etc.",
                next_state=ConversationState.ORDER_PLACEMENT_SELECTING_DISTRICT
            )

        session.set_context('selected_district', matching_district)

        # Get locations for this district
        locations = [item for item in DELIVERY_RATES if item['district'] == matching_district]

        if len(locations) == 1:
            # Only one location in district
            loc = locations[0]
            session.set_context('selected_location', loc['location'])
            session.set_context('delivery_charge', loc['rate'])
            session.set_state(ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK)
            return self.response(
                f"📍 **District:** {matching_district}\n"
                f"📍 **Location:** {loc['location']}\n"
                f"🚚 **Delivery Charge:** Rs. {loc['rate']}\n\n"
                f"🏠 Please enter any **landmark** near your delivery address\n"
                f"(or type 'skip' if none):",
                next_state=ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK
            )

        # Multiple locations - let user choose
        session.set_context('available_locations', locations)
        session.set_state(ConversationState.ORDER_PLACEMENT_SELECTING_LOCATION)

        location_list = "\n".join([f"📍 {loc['location']} - Rs. {loc['rate']}" for loc in locations[:15]])

        return self.response(
            f"✅ **District:** {matching_district}\n\n"
            f"🗺️ Select your location (with delivery rates):\n\n"
            f"{location_list}\n\n"
            f"👆 Type your location name:",
            next_state=ConversationState.ORDER_PLACEMENT_SELECTING_LOCATION
        )

    def process_location_selection(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process location selection within district"""
        locations = session.get_context('available_locations', [])
        user_input = message.strip()

        # Find matching location
        matching_loc = None
        for loc in locations:
            if loc['location'].lower() == user_input.lower():
                matching_loc = loc
                break

        if not matching_loc:
            for loc in locations:
                if user_input.lower() in loc['location'].lower() or loc['location'].lower() in user_input.lower():
                    matching_loc = loc
                    break

        if not matching_loc:
            location_list = "\n".join([f"📍 {loc['location']} - Rs. {loc['rate']}" for loc in locations[:10]])
            return self.response(
                f"⚠️ Location not found. Please select from:\n\n{location_list}",
                next_state=ConversationState.ORDER_PLACEMENT_SELECTING_LOCATION
            )

        session.set_context('selected_location', matching_loc['location'])
        session.set_context('delivery_charge', matching_loc['rate'])
        session.set_state(ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK)

        return self.response(
            f"📍 **Location:** {matching_loc['location']}\n"
            f"🚚 **Delivery Charge:** Rs. {matching_loc['rate']}\n\n"
            f"🏠 Please enter any **landmark** near your delivery address\n"
            f"(or type 'skip' if none):",
            next_state=ConversationState.ORDER_PLACEMENT_AWAITING_LANDMARK
        )

    def process_landmark(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process landmark input and show final summary"""
        if self.is_skip(message):
            session.set_context('landmark', '')
        else:
            session.set_context('landmark', message.strip())

        # Show order summary
        return self.show_order_summary(session)

    def show_order_summary(self, session: SessionData) -> HandlerResponse:
        """Display order summary for confirmation"""
        ctx = session.state_context
        product = ctx.get('selected_product', {})
        quantity = ctx.get('quantity', 1)
        name = ctx.get('customer_name', '')
        phone = ctx.get('contact_number', '')
        district = ctx.get('selected_district', '')
        location = ctx.get('selected_location', '')
        landmark = ctx.get('landmark', '')
        delivery_charge = ctx.get('delivery_charge', 100)

        price = product.get('price', 0)
        subtotal = price * quantity
        total = subtotal + delivery_charge

        summary = "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        summary += "📋 **ORDER SUMMARY**\n"
        summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        summary += f"🛍️ **Product:** {product.get('name', 'Product')[:45]}\n"
        summary += f"🔢 **Quantity:** {quantity}\n"
        summary += f"💰 **Price:** {self.format_price(price)} × {quantity} = {self.format_price(subtotal)}\n\n"

        summary += "📦 **Delivery Details:**\n"
        summary += f"  👤 Name: {name}\n"
        summary += f"  📱 Phone: {phone}\n"
        summary += f"  📍 District: {district}\n"
        summary += f"  📍 Location: {location}\n"
        if landmark:
            summary += f"  🏠 Landmark: {landmark}\n"

        summary += "\n💳 **Payment Details:**\n"
        summary += f"  • Subtotal: {self.format_price(subtotal)}\n"
        summary += f"  • Delivery: Rs. {delivery_charge}\n"
        summary += f"  • **Total: {self.format_price(total)}** 💵\n"
        summary += f"  • Method: Cash on Delivery 💰\n"

        summary += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        summary += "✅ **Confirm this order?** (Yes/No)"

        session.set_state(ConversationState.ORDER_PLACEMENT_CONFIRMING)
        return self.response(
            summary,
            products=[product],
            next_state=ConversationState.ORDER_PLACEMENT_CONFIRMING
        )

    def process_confirmation(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process final order confirmation"""
        if self.is_rejection(message) or 'cancel' in message.lower():
            session.reset_state()
            return self.response(
                "❌ Order cancelled. Is there anything else I can help you with? 😊",
                reset_state=True
            )

        if self.is_confirmation(message) or 'confirm' in message.lower():
            return self.place_order(session)

        return self.response(
            "🤔 Please type 'Yes' to confirm your order or 'No' to cancel.",
            next_state=ConversationState.ORDER_PLACEMENT_CONFIRMING
        )

    def place_order(self, session: SessionData) -> HandlerResponse:
        """Submit order to Django backend"""
        ctx = session.state_context
        product = ctx.get('selected_product', {})
        quantity = ctx.get('quantity', 1)
        delivery_charge = ctx.get('delivery_charge', 100)
        district = ctx.get('selected_district', '')
        location = ctx.get('selected_location', '')
        landmark = ctx.get('landmark', '')

        # Build location string
        full_location = f"{location}, {district}"

        order_data = {
            'customer_name': ctx.get('customer_name', ''),
            'contact_number': ctx.get('contact_number', ''),
            'location': full_location,
            'landmark': landmark,
            'payment_method': 'cod',
            'delivery_charge': delivery_charge,
            'items': [{
                'product_id': product.get('id'),
                'quantity': quantity
            }]
        }

        result = self.api.create_order(order_data)
        session.reset_state()

        if result.get('success'):
            order_number = result.get('order_number', result.get('order_id', 'N/A'))
            price = product.get('price', 0)
            subtotal = price * quantity
            total = subtotal + delivery_charge

            return self.response(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🎉 **ORDER PLACED SUCCESSFULLY!** ✅\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔖 **Order Number:** #{order_number}\n\n"
                f"📦 **Order Details:**\n"
                f"  🛍️ Product: {product.get('name', 'Product')[:40]}\n"
                f"  🔢 Quantity: {quantity}\n"
                f"  💰 Subtotal: {self.format_price(subtotal)}\n"
                f"  🚚 Delivery: Rs. {delivery_charge}\n"
                f"  💵 **Total: {self.format_price(total)}**\n\n"
                f"📍 **Delivery To:**\n"
                f"  👤 {ctx.get('customer_name', '')}\n"
                f"  📱 {ctx.get('contact_number', '')}\n"
                f"  📍 {full_location}\n"
                + (f"  🏠 Near: {landmark}\n" if landmark else "") +
                f"\n💰 **Payment:** Cash on Delivery\n"
                f"📅 **Estimated Delivery:** 3-5 business days\n\n"
                f"📝 Save your order number **#{order_number}** to track your order!\n\n"
                f"🙏 Thank you for shopping with OVN Store! 💜",
                reset_state=True
            )
        else:
            error = result.get('error', 'Unknown error')
            return self.response(
                f"😔 Sorry, there was an error placing your order:\n{error}\n\n"
                f"Please try again or contact support. 📞",
                reset_state=True
            )

    # Helper methods
    def format_product_card(self, product: Dict) -> str:
        """Format product info for display"""
        name = product.get('name', 'Product')
        price = product.get('price', 0)
        rating = product.get('rating', 0)
        stars = '⭐' * int(rating) + '☆' * (5 - int(rating))

        text = f"🛍️ **{name}**\n"
        text += f"💰 Price: **{self.format_price(price)}**\n"
        if rating > 0:
            text += f"⭐ Rating: {stars} ({rating:.1f})"
        return text

    def format_product_details(self, product: Dict) -> str:
        """Format detailed product info"""
        name = product.get('name', 'Product')
        price = product.get('price', 0)
        description = product.get('description', 'No description available.')
        rating = product.get('rating', 0)
        review_count = product.get('review_count', 0)
        stars = '⭐' * int(rating) + '☆' * (5 - int(rating))

        text = "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"🛍️ **{name}**\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"💰 **Price:** {self.format_price(price)}\n"
        if rating > 0:
            text += f"⭐ **Rating:** {stars} ({rating:.1f}) - {review_count} reviews\n"
        text += f"\n📝 **Description:**\n{description[:300]}"
        if len(description) > 300:
            text += "..."
        return text

    def is_skip(self, message: str) -> bool:
        """Check if user wants to skip"""
        skip_words = ['skip', 'none', 'no', 'nothing', 'na', 'n/a', '-']
        return message.strip().lower() in skip_words
