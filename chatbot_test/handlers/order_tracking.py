"""
Order Tracking Handler for OVN Store Chatbot
Handles order status queries and tracking
"""
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .base import BaseHandler, HandlerResponse
from core.session import SessionData, ConversationState


class OrderTrackingHandler(BaseHandler):
    """
    Handles order tracking:
    - Track order by ID
    - Track order by phone number
    - Show order details
    """

    def can_handle(self, intent: str, state: ConversationState) -> bool:
        """Handle order tracking intent or active tracking states"""
        if intent == 'order_tracking' and state == ConversationState.IDLE:
            return True
        tracking_states = [
            ConversationState.ORDER_TRACKING_START,
            ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER,
            ConversationState.ORDER_TRACKING_SELECTING_ORDER
        ]
        return state in tracking_states

    def handle(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process order tracking request"""
        state = session.state

        # Initial request
        if state == ConversationState.IDLE:
            return self.start_tracking(message, session, entities)

        # Waiting for order ID or phone
        elif state == ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER:
            return self.process_identifier(message, session, entities)

        # Selecting from multiple orders
        elif state == ConversationState.ORDER_TRACKING_SELECTING_ORDER:
            return self.process_order_selection(message, session, entities)

        return self.response("📦 I can help you track your order. Please provide your order ID or phone number.")

    def start_tracking(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Start order tracking flow"""
        # Check if identifier provided in initial message
        phone = entities.get('phone')
        order_id = entities.get('order_id')

        if phone:
            session.remember_user_info(phone=phone)
            return self.fetch_orders_by_phone(phone, session)

        if order_id:
            return self.fetch_order_by_id(order_id, session)

        # Check if we have saved phone
        if session.user_phone:
            session.set_state(ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER)
            return self.response(
                f"📱 Would you like to track orders for **{session.user_phone}**?",
                next_state=ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER,
                quick_replies=['Yes', 'Use Different Number', 'Use Order ID']
            )

        # Ask for identifier
        session.set_state(ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER)
        return self.response(
            "📦 I can help you track your order!\n\nPlease provide:\n• 🔖 Your **order ID** (e.g., ABC12345)\n• 📱 Or your **phone number**",
            next_state=ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER,
            quick_replies=['Use Phone Number', 'Use Order ID']
        )

    def process_identifier(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process identifier input (phone or order ID)"""
        msg = message.strip().lower()

        # Check for confirmation to use saved phone
        if self.is_confirmation(message) and session.user_phone:
            return self.fetch_orders_by_phone(session.user_phone, session)

        # Check if user is re-asking to track (not providing identifier)
        tracking_phrases = ['track', 'check', 'order', 'where', 'status', 'find']
        if any(phrase in msg for phrase in tracking_phrases) and len(msg.split()) > 1:
            # This is a tracking request, not an identifier - restart flow
            if session.user_phone:
                return self.response(
                    f"📱 Would you like to track orders for **{session.user_phone}**?",
                    next_state=ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER,
                    quick_replies=['Yes', 'Use Different Number', 'Use Order ID']
                )
            return self.response(
                "📦 Please provide your **order ID** or **phone number** to track your order.",
                next_state=ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER
            )

        # Check for new phone
        phone = entities.get('phone')
        if phone:
            session.remember_user_info(phone=phone)
            return self.fetch_orders_by_phone(phone, session)

        # Check for order ID from entities
        order_id = entities.get('order_id')
        if order_id:
            return self.fetch_order_by_id(order_id, session)

        # Check if message looks like a phone number (10 digits)
        digits = ''.join(filter(str.isdigit, message))
        if len(digits) == 10:
            session.remember_user_info(phone=digits)
            return self.fetch_orders_by_phone(digits, session)

        # Check if it looks like a valid order ID (alphanumeric, 6-36 chars, no spaces)
        cleaned = message.strip()
        if len(cleaned) >= 6 and len(cleaned) <= 36 and ' ' not in cleaned:
            # Looks like an order ID (no spaces, reasonable length)
            return self.fetch_order_by_id(cleaned, session)

        return self.response(
            "⚠️ I couldn't recognize that. Please provide a valid:\n• 📱 10-digit phone number\n• 🔖 Or order ID",
            next_state=ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER
        )

    def process_order_selection(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process order selection from list"""
        orders = session.get_context('orders', [])

        if not orders:
            session.reset_state()
            return self.response(
                "😕 Something went wrong. Let's start over - please provide your phone or order ID.",
                reset_state=True
            )

        # Check for number selection
        try:
            selection = int(message.strip())
            if 1 <= selection <= len(orders):
                order = orders[selection - 1]
                return self.show_order_detail(order, session)
        except ValueError:
            pass

        # Check if they typed order number
        for order in orders:
            order_num = order.get('order_number', order.get('order_id', ''))
            if message.strip().upper() in str(order_num).upper():
                return self.show_order_detail(order, session)

        return self.response(
            f"👆 Please select a number from 1 to {len(orders)}, or type the order number.",
            next_state=ConversationState.ORDER_TRACKING_SELECTING_ORDER
        )

    def fetch_orders_by_phone(self, phone: str, session: SessionData) -> HandlerResponse:
        """Fetch orders by phone number"""
        result = self.api.get_orders_by_phone(phone)

        if not result.get('success', True) and result.get('error'):
            session.reset_state()
            return self.response(
                f"😔 Error: {result.get('error')}\nPlease try again.",
                reset_state=True,
                quick_replies=['Try Again', 'Browse Products']
            )

        orders = result.get('orders', [])

        if not orders:
            session.reset_state()
            return self.response(
                f"📭 No orders found for phone **{phone}**.\n\nMake sure you're using the same number you placed the order with.",
                reset_state=True,
                quick_replies=['Try Different Number', 'Browse Products']
            )

        if len(orders) == 1:
            return self.show_order_detail(orders[0], session)

        # Multiple orders - let user select
        session.set_context('orders', orders)
        session.set_state(ConversationState.ORDER_TRACKING_SELECTING_ORDER)

        order_list = ""
        for i, order in enumerate(orders[:10], 1):  # Limit to 10
            status = order.get('status_display', order.get('status', 'Unknown'))
            order_num = order.get('order_number', order.get('order_id', 'N/A'))[:8]
            total = order.get('total_amount', 0)
            date = order.get('created_at', '')[:10]
            order_list += f"{i}. **#{order_num}** - {status} - Rs. {total:,.0f} ({date})\n"

        return self.response(
            f"📦 Found **{len(orders)}** orders for **{phone}**:\n\n{order_list}\n👆 Which order would you like details for? (Enter number)",
            next_state=ConversationState.ORDER_TRACKING_SELECTING_ORDER,
            quick_replies=[f"{i}" for i in range(1, min(len(orders) + 1, 5))]
        )

    def fetch_order_by_id(self, order_id: str, session: SessionData) -> HandlerResponse:
        """Fetch order by order ID"""
        result = self.api.get_order_detail(order_id, contact=session.user_phone)

        if not result.get('success', True) and result.get('error'):
            # If guest order, might need phone
            if 'phone' in result.get('error', '').lower() or 'contact' in result.get('error', '').lower():
                session.set_context('pending_order_id', order_id)
                session.set_state(ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER)
                return self.response(
                    "📱 This appears to be a guest order. Please provide the phone number used when placing the order.",
                    next_state=ConversationState.ORDER_TRACKING_AWAITING_IDENTIFIER
                )

            session.reset_state()
            return self.response(
                f"😕 I couldn't find order **{order_id}**. Please check the order ID and try again.",
                reset_state=True,
                quick_replies=['Try Again', 'Use Phone Number']
            )

        order = result.get('order', result)
        return self.show_order_detail(order, session)

    def show_order_detail(self, order: Dict, session: SessionData) -> HandlerResponse:
        """Display detailed order information with customer details and product images"""
        session.reset_state()

        status_emoji = {
            'processing': '📦', 'confirmed': '✅', 'packed': '📦',
            'shipped': '🚚', 'delivered': '✅', 'cancelled': '❌', 'returned': '↩️'
        }

        order_num = order.get('order_number', order.get('order_id', 'N/A'))
        status = order.get('status', 'unknown')
        status_display = order.get('status_display', status.title())
        emoji = status_emoji.get(status, '📋')
        payment = order.get('payment_status', 'pending').title()

        # Parse shipping address to extract customer details
        # Format: "Customer Name\nPhone\nLocation\nLandmark: ..."
        shipping_address = order.get('shipping_address', '')
        address_lines = shipping_address.split('\n') if shipping_address else []

        customer_name = address_lines[0] if len(address_lines) > 0 else 'N/A'
        customer_phone = address_lines[1] if len(address_lines) > 1 else 'N/A'
        customer_location = address_lines[2] if len(address_lines) > 2 else 'N/A'
        landmark = ''
        if len(address_lines) > 3:
            landmark_line = address_lines[3]
            if landmark_line.startswith('Landmark:'):
                landmark = landmark_line.replace('Landmark:', '').strip()

        # Get items and recalculate correct subtotal from current prices
        items = order.get('items', [])
        correct_subtotal = 0
        for item in items:
            unit_price = item.get('unit_price', 0)
            quantity = item.get('quantity', 1)
            correct_subtotal += unit_price * quantity

        # Amounts - use recalculated subtotal
        subtotal = correct_subtotal  # Use correct price, not stored wrong price
        shipping_cost = order.get('shipping_cost', 0)
        discount = order.get('discount_amount', 0)
        total = subtotal + shipping_cost - discount  # Recalculate total

        response = f"**Order #{order_num}** {emoji}\n"
        response += "━━━━━━━━━━━━━━━━━━━━\n\n"

        # Customer Details Section
        response += "**👤 Customer Details:**\n"
        response += f"  • Name: {customer_name}\n"
        response += f"  • Phone: {customer_phone}\n"
        response += f"  • Location: {customer_location}\n"
        if landmark:
            response += f"  • Landmark: {landmark}\n"

        response += "\n"

        # Order Status Section
        response += "**📋 Order Status:**\n"
        response += f"  • Status: {status_display}\n"
        response += f"  • Payment: {payment}\n"

        # Tracking number
        tracking = order.get('tracking_number')
        if tracking:
            response += f"  • Tracking #: {tracking}\n"

        response += "\n"

        # Items Section - header only, products shown as cards below
        if items:
            response += f"**🛒 Items Ordered ({len(items)}):**\n"
            response += "_See product cards below for details_\n"

        response += "\n"

        # Price Breakdown Section
        response += "**💰 Price Breakdown:**\n"
        response += f"  • Subtotal: Rs. {subtotal:,.2f}\n"
        response += f"  • Delivery Charge: Rs. {shipping_cost:,.2f}\n"
        if discount > 0:
            response += f"  • Discount: -Rs. {discount:,.2f}\n"
        response += f"  • **Total: Rs. {total:,.2f}**\n"

        # Order Date
        created_at = order.get('created_at', '')
        if created_at:
            response += f"\n📅 Order Date: {created_at[:16]}"

        # Order history/timeline
        history = order.get('history', [])
        if history:
            response += "\n\n**📍 Timeline:**"
            for event in history[-3:]:  # Last 3 events
                event_action = event.get('action', event.get('status', ''))
                event_date = event.get('created_at', '')[:10]
                response += f"\n  • {event_action} - {event_date}"

        # Add status-specific helpful message
        response += "\n\n"
        response += "━━━━━━━━━━━━━━━━━━━━\n"
        if status in ['processing', 'confirmed', 'packed']:
            response += "🚀 Your order is being processed and will be delivered within **3-5 business days**. Thank you for shopping with us! 💜"
        elif status == 'shipped':
            response += "🚚 Your order is on the way! Expected delivery within **1-2 days**. Thank you for your patience! 💜"
        elif status == 'delivered':
            response += "✅ Your order has been delivered! We hope you love your purchase. Thank you for shopping with us! 💜"
        elif status == 'cancelled':
            response += "❌ This order was cancelled. If you have any questions, please contact our support team."
        else:
            response += "📦 Thank you for your order! If you have any questions, feel free to ask. 💜"

        # Format order items as products for display with images
        order_items_as_products = []
        items_count = len(items)

        for item in items[:8]:  # Limit to 8 items
            unit_price = item.get('unit_price', 0)
            quantity = item.get('quantity', 1)
            item_total = unit_price * quantity

            order_items_as_products.append({
                'id': item.get('product_id'),
                'name': item.get('product_name', 'Product'),
                'image': item.get('product_image', ''),
                'price': unit_price,
                'quantity': quantity,
                'item_total': item_total,
                'delivery_charge': shipping_cost if items_count == 1 else None,
                'order_total': total if items_count == 1 else None,  # Use already calculated total
                'is_order_item': True
            })

        return self.response(
            response,
            products=order_items_as_products,
            reset_state=True,
            quick_replies=['Track Another Order', 'Browse Products', 'Get Help']
        )
