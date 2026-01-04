"""
Review Handler for OVN Store Chatbot
Handles viewing and submitting product reviews
"""
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .base import BaseHandler, HandlerResponse
from .product import ProductHandler
from core.session import SessionData, ConversationState


class ReviewHandler(BaseHandler):
    """
    Handles product reviews:
    - View reviews for a product
    - Submit a new review
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_handler = ProductHandler()

    def can_handle(self, intent: str, state: ConversationState) -> bool:
        """Handle review intents or active review states"""
        if intent in ['review_view', 'review_submit'] and state == ConversationState.IDLE:
            return True
        review_states = [
            ConversationState.REVIEW_SELECTING_PRODUCT,
            ConversationState.REVIEW_AWAITING_RATING,
            ConversationState.REVIEW_AWAITING_TITLE,
            ConversationState.REVIEW_AWAITING_COMMENT,
            ConversationState.REVIEW_CONFIRMING
        ]
        return state in review_states

    def handle(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process review request"""
        state = session.state
        intent = entities.get('intent', '')

        # View reviews
        if state == ConversationState.IDLE and intent == 'review_view':
            return self.show_reviews(message, session, entities)

        # Submit review flow
        if state == ConversationState.IDLE and intent == 'review_submit':
            return self.start_review(message, session, entities)

        elif state == ConversationState.REVIEW_SELECTING_PRODUCT:
            return self.process_product_selection(message, session, entities)

        elif state == ConversationState.REVIEW_AWAITING_RATING:
            return self.process_rating(message, session, entities)

        elif state == ConversationState.REVIEW_AWAITING_TITLE:
            return self.process_title(message, session, entities)

        elif state == ConversationState.REVIEW_AWAITING_COMMENT:
            return self.process_comment(message, session, entities)

        elif state == ConversationState.REVIEW_CONFIRMING:
            return self.process_confirmation(message, session, entities)

        return self.response(
            "Would you like to view reviews or write a review?",
            quick_replies=['View Reviews', 'Write Review']
        )

    def show_reviews(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Show reviews for a product"""
        # Find product from message
        from core.intent import EntityExtractor
        extractor = EntityExtractor()
        keywords = extractor.extract_product_keywords(message)

        product = None
        if keywords:
            product = self.product_handler.find_product_by_name(' '.join(keywords))

        # Check session for recently viewed products
        if not product and session.last_viewed_products:
            product = session.last_viewed_products[0]

        if not product:
            products = self.product_handler.get_featured_products(limit=4)
            if products:
                session.set_context('product_options', products)
                session.set_context('review_action', 'view')
                session.set_state(ConversationState.REVIEW_SELECTING_PRODUCT)
                return self.response(
                    "Which product would you like to see reviews for?",
                    products=products,
                    next_state=ConversationState.REVIEW_SELECTING_PRODUCT
                )
            return self.response(
                "Please specify which product you'd like to see reviews for.",
                quick_replies=['Show Products', 'Browse All']
            )

        # Fetch reviews from API
        return self.fetch_and_display_reviews(product, session)

    def fetch_and_display_reviews(self, product: Dict, session: SessionData) -> HandlerResponse:
        """Fetch and display reviews for a product"""
        product_id = product.get('id')
        result = self.api.get_product_reviews(product_id)

        if not result.get('success', True) and result.get('error'):
            return self.response(
                f"Couldn't load reviews: {result.get('error')}",
                quick_replies=['Try Again', 'Browse Products']
            )

        reviews = result.get('reviews', [])
        avg_rating = result.get('average_rating', 0)
        total_reviews = result.get('total_reviews', 0)

        product_name = product.get('name', 'Product')[:40]

        if not reviews:
            return self.response(
                f"**{product_name}**\n\nNo reviews yet for this product. Be the first to review!",
                products=[product],
                quick_replies=['Write Review', 'Browse Products']
            )

        # Format reviews
        stars = '★' * int(avg_rating) + '☆' * (5 - int(avg_rating))
        response = f"**{product_name}**\n\n"
        response += f"**Overall Rating:** {stars} ({avg_rating}/5 from {total_reviews} reviews)\n\n"

        # Show rating distribution if available
        distribution = result.get('rating_distribution', {})
        if distribution:
            response += "**Rating Distribution:**\n"
            for rating in range(5, 0, -1):
                count = distribution.get(str(rating), 0)
                bar = '█' * min(count, 10)
                response += f"  {rating}★ {bar} ({count})\n"
            response += "\n"

        # Show top reviews
        response += "**Recent Reviews:**\n\n"
        for review in reviews[:5]:
            user = review.get('user', 'Anonymous')
            rating = review.get('rating', 0)
            review_stars = '★' * rating
            title = review.get('title', '')
            comment = review.get('comment', '')[:150]
            verified = ' ✓' if review.get('is_verified_purchase') else ''

            response += f"**{user}** {review_stars}{verified}\n"
            if title:
                response += f"*{title}*\n"
            response += f"{comment}...\n\n"

        return self.response(
            response,
            products=[product],
            quick_replies=['Write Review', 'See More', 'Browse Products']
        )

    def start_review(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Start review submission flow"""
        # Find product from message
        from core.intent import EntityExtractor
        extractor = EntityExtractor()
        keywords = extractor.extract_product_keywords(message)

        product = None
        if keywords:
            product = self.product_handler.find_product_by_name(' '.join(keywords))

        # Check session for recently viewed products
        if not product and session.last_viewed_products:
            product = session.last_viewed_products[0]

        if product:
            # Check if user can review
            return self.check_and_start_review(product, session)

        # Show product selection
        products = self.product_handler.get_all_products(limit=6)
        if products:
            session.set_context('product_options', products)
            session.set_context('review_action', 'submit')
            session.set_state(ConversationState.REVIEW_SELECTING_PRODUCT)
            return self.response(
                "Which product would you like to review?",
                products=products,
                next_state=ConversationState.REVIEW_SELECTING_PRODUCT
            )

        return self.response(
            "Please specify which product you'd like to review.",
            quick_replies=['Show Products']
        )

    def check_and_start_review(self, product: Dict, session: SessionData) -> HandlerResponse:
        """Check eligibility and start review"""
        product_id = product.get('id')
        result = self.api.can_review_product(product_id)

        can_review = result.get('can_review', False)

        if not can_review:
            reason = result.get('reason', 'unknown')
            message_map = {
                'login_required': "You need to be logged in to write a review.",
                'already_reviewed': "You've already reviewed this product.",
                'no_purchase': "You can only review products from your delivered orders."
            }
            msg = result.get('message') or message_map.get(reason, "Unable to review at this time.")

            return self.response(
                f"**{product.get('name', 'Product')[:40]}**\n\n{msg}",
                products=[product],
                quick_replies=['View Reviews', 'Browse Products']
            )

        # Can review - start flow
        session.set_context('product', product)
        session.set_context('order_id', result.get('order_id'))
        session.set_state(ConversationState.REVIEW_AWAITING_RATING)

        return self.response(
            f"**Review: {product.get('name', 'Product')[:40]}**\n\n"
            f"How would you rate this product? (1-5 stars)",
            products=[product],
            next_state=ConversationState.REVIEW_AWAITING_RATING,
            quick_replies=['⭐ 1', '⭐⭐ 2', '⭐⭐⭐ 3', '⭐⭐⭐⭐ 4', '⭐⭐⭐⭐⭐ 5']
        )

    def process_product_selection(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process product selection for review"""
        products = session.get_context('product_options', [])
        action = session.get_context('review_action', 'view')

        # Check for number selection
        try:
            selection = int(message.strip().replace('⭐', '').strip())
            if 1 <= selection <= len(products):
                product = products[selection - 1]
                if action == 'view':
                    session.reset_state()
                    return self.fetch_and_display_reviews(product, session)
                else:
                    return self.check_and_start_review(product, session)
        except ValueError:
            pass

        # Try to find product by name
        product = self.product_handler.find_product_by_name(message)
        if product:
            if action == 'view':
                session.reset_state()
                return self.fetch_and_display_reviews(product, session)
            else:
                return self.check_and_start_review(product, session)

        return self.response(
            "Please select a product from the list or search for a specific product.",
            products=products,
            next_state=ConversationState.REVIEW_SELECTING_PRODUCT
        )

    def process_rating(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process rating input"""
        # Extract rating
        rating = entities.get('rating')
        if not rating:
            from core.intent import EntityExtractor
            extractor = EntityExtractor()
            rating = extractor.extract_rating(message)

        # Try to extract from star emojis
        if not rating:
            star_count = message.count('⭐') or message.count('★')
            if 1 <= star_count <= 5:
                rating = star_count

        if not rating or not (1 <= rating <= 5):
            return self.response(
                "Please rate from 1 to 5 stars.",
                next_state=ConversationState.REVIEW_AWAITING_RATING,
                quick_replies=['1', '2', '3', '4', '5']
            )

        session.set_context('rating', rating)
        session.set_state(ConversationState.REVIEW_AWAITING_TITLE)

        stars = '★' * rating + '☆' * (5 - rating)
        return self.response(
            f"Rating: {stars}\n\nGive your review a short title (or type 'skip'):",
            next_state=ConversationState.REVIEW_AWAITING_TITLE,
            quick_replies=['Skip']
        )

    def process_title(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process review title"""
        if self.is_skip(message):
            session.set_context('title', '')
        else:
            session.set_context('title', message.strip()[:100])

        session.set_state(ConversationState.REVIEW_AWAITING_COMMENT)
        return self.response(
            "Now write your review. Share your experience with this product:",
            next_state=ConversationState.REVIEW_AWAITING_COMMENT
        )

    def process_comment(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process review comment"""
        if len(message.strip()) < 10:
            return self.response(
                "Please write a bit more about your experience (at least 10 characters).",
                next_state=ConversationState.REVIEW_AWAITING_COMMENT
            )

        session.set_context('comment', message.strip()[:500])

        # Show summary
        return self.show_review_summary(session)

    def show_review_summary(self, session: SessionData) -> HandlerResponse:
        """Show review summary for confirmation"""
        ctx = session.state_context
        product = ctx.get('product', {})
        rating = ctx.get('rating', 0)
        title = ctx.get('title', '')
        comment = ctx.get('comment', '')[:200]

        stars = '★' * rating + '☆' * (5 - rating)

        summary = f"**Review Summary**\n\n"
        summary += f"**Product:** {product.get('name', 'Product')[:40]}\n"
        summary += f"**Rating:** {stars}\n"
        if title:
            summary += f"**Title:** {title}\n"
        summary += f"**Review:** {comment}...\n\n"
        summary += "**Submit this review?**"

        session.set_state(ConversationState.REVIEW_CONFIRMING)
        return self.response(
            summary,
            products=[product],
            next_state=ConversationState.REVIEW_CONFIRMING,
            quick_replies=['Submit', 'Cancel']
        )

    def process_confirmation(self, message: str, session: SessionData, entities: Dict) -> HandlerResponse:
        """Process review confirmation"""
        if self.is_rejection(message) or 'cancel' in message.lower():
            session.reset_state()
            return self.response(
                "Review cancelled. Is there anything else I can help with?",
                reset_state=True,
                quick_replies=['Browse Products', 'Track Order']
            )

        if self.is_confirmation(message) or 'submit' in message.lower():
            return self.submit_review(session)

        return self.response(
            "Please type 'submit' to post your review or 'cancel' to cancel.",
            next_state=ConversationState.REVIEW_CONFIRMING,
            quick_replies=['Submit', 'Cancel']
        )

    def submit_review(self, session: SessionData) -> HandlerResponse:
        """Submit review to backend"""
        ctx = session.state_context
        product = ctx.get('product', {})
        product_id = product.get('id')

        review_data = {
            'rating': ctx.get('rating'),
            'title': ctx.get('title', ''),
            'comment': ctx.get('comment', ''),
            'order_id': ctx.get('order_id')
        }

        result = self.api.submit_review(product_id, review_data)
        session.reset_state()

        if result.get('success'):
            return self.response(
                f"**Review Submitted!** ✅\n\n"
                f"Thank you for reviewing **{product.get('name', 'this product')[:40]}**!\n\n"
                f"Your review will be visible after approval.",
                reset_state=True,
                quick_replies=['Write Another Review', 'Browse Products']
            )
        else:
            error = result.get('error', 'Unknown error')
            return self.response(
                f"Sorry, there was an error submitting your review:\n{error}",
                reset_state=True,
                quick_replies=['Try Again', 'Browse Products']
            )
