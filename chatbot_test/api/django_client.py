"""
Django Backend API Client for OVN Store Chatbot
Handles all communication with Django backend APIs
"""
import requests
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DJANGO_BASE_URL


class DjangoAPIClient:
    """
    Client for Django backend APIs.
    Handles orders, reviews, contacts, and authentication.
    """

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or DJANGO_BASE_URL).rstrip('/')
        self.session = requests.Session()
        self.timeout = 10  # seconds

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            return {'success': False, 'error': 'Request timed out. Please try again.'}
        except requests.ConnectionError:
            return {'success': False, 'error': 'Could not connect to server.'}
        except requests.HTTPError as e:
            try:
                error_data = e.response.json()
                return {'success': False, 'error': error_data.get('error', str(e))}
            except:
                return {'success': False, 'error': f'Server error: {e.response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ==================== Order APIs ====================

    def create_order(self, order_data: Dict) -> Dict:
        """
        Create a new order.

        Args:
            order_data: {
                'customer_name': str,
                'contact_number': str (10 digits),
                'location': str,
                'landmark': str (optional),
                'payment_method': 'cod',
                'email': str (optional),
                'items': [{'product_id': int, 'quantity': int}]
            }

        Returns:
            {success, order_id, order_number, message} or {success: False, error}
        """
        return self._make_request('POST', '/orders/api/create/', json=order_data)

    def get_orders_by_phone(self, phone: str) -> Dict:
        """
        Get orders by phone number (for guest tracking).

        Args:
            phone: 10-digit phone number

        Returns:
            {success, orders: [...]} or {success: False, error}
        """
        return self._make_request('GET', '/orders/api/my-orders/', params={'contact': phone})

    def get_order_detail(self, order_id: str, contact: str = None) -> Dict:
        """
        Get detailed order information.

        Args:
            order_id: Order UUID or short ID
            contact: Phone number (required for guest orders)

        Returns:
            {success, order: {...}} or {success: False, error}
        """
        params = {'contact': contact} if contact else {}
        return self._make_request('GET', f'/orders/api/{order_id}/', params=params)

    def check_login_status(self) -> Dict:
        """
        Check if user is logged in and get discount info.

        Returns:
            {is_logged_in, discount_percent, username}
        """
        return self._make_request('GET', '/orders/api/check-login/')

    # ==================== Review APIs ====================

    def get_product_reviews(self, product_id: int) -> Dict:
        """
        Get reviews for a product.

        Args:
            product_id: Product ID

        Returns:
            {success, reviews: [...], average_rating, total_reviews, rating_distribution}
        """
        return self._make_request('GET', f'/api/products/{product_id}/reviews/')

    def can_review_product(self, product_id: int) -> Dict:
        """
        Check if current user can review a product.

        Args:
            product_id: Product ID

        Returns:
            {can_review: bool, reason, message, order_id (if can review)}
        """
        return self._make_request('GET', f'/api/products/{product_id}/can-review/')

    def submit_review(self, product_id: int, review_data: Dict) -> Dict:
        """
        Submit a product review.

        Args:
            product_id: Product ID
            review_data: {
                'rating': int (1-5),
                'title': str,
                'comment': str,
                'order_id': str (optional, for verification)
            }

        Returns:
            {success, message} or {success: False, error}
        """
        return self._make_request('POST', f'/api/products/{product_id}/submit-review/', json=review_data)

    # ==================== Contact/Support APIs ====================

    def submit_contact(self, contact_data: Dict) -> Dict:
        """
        Submit a contact/support form.

        Args:
            contact_data: {
                'name': str,
                'email': str,
                'phone': str (optional),
                'subject': str (order, product, complaint, return, feedback, general),
                'message': str
            }

        Returns:
            {success, id, message} or {success: False, error}
        """
        return self._make_request('POST', '/api/contact/', json=contact_data)

    # ==================== Auth APIs ====================

    def check_auth_status(self) -> Dict:
        """
        Check authentication status.

        Returns:
            {is_authenticated, user: {...} or None}
        """
        return self._make_request('GET', '/api/auth-status/')

    # ==================== Product APIs ====================

    def get_products(self, limit: int = 20) -> Dict:
        """Get all products"""
        return self._make_request('GET', '/api/products/list/', params={'limit': limit})

    def get_product_detail(self, product_id: int) -> Dict:
        """Get single product details"""
        return self._make_request('GET', f'/api/products/{product_id}/')

    def get_flash_sale_products(self) -> Dict:
        """Get flash sale products"""
        return self._make_request('GET', '/api/products/flash-sale/')

    def get_categories(self) -> Dict:
        """Get all categories"""
        return self._make_request('GET', '/api/products/categories/')

    # ==================== Utility Methods ====================

    def format_order_for_display(self, order: Dict) -> Dict:
        """Format order data for chatbot display"""
        status_emoji = {
            'processing': '📦',
            'confirmed': '✅',
            'packed': '📦',
            'shipped': '🚚',
            'delivered': '✅',
            'cancelled': '❌',
            'returned': '↩️'
        }

        return {
            'order_number': order.get('order_number', order.get('order_id', 'N/A')),
            'status': order.get('status', 'unknown'),
            'status_display': order.get('status_display', order.get('status', 'Unknown').title()),
            'status_emoji': status_emoji.get(order.get('status', ''), ''),
            'total': order.get('total_amount', 0),
            'payment_status': order.get('payment_status', 'pending'),
            'items': order.get('items', []),
            'shipping_address': order.get('shipping_address', ''),
            'tracking_number': order.get('tracking_number', ''),
            'created_at': order.get('created_at', '')
        }

    def format_review_for_display(self, review: Dict) -> Dict:
        """Format review data for chatbot display"""
        return {
            'user': review.get('user', 'Anonymous'),
            'rating': review.get('rating', 0),
            'stars': '★' * review.get('rating', 0) + '☆' * (5 - review.get('rating', 0)),
            'title': review.get('title', ''),
            'comment': review.get('comment', '')[:200],
            'is_verified': review.get('is_verified_purchase', False),
            'date': review.get('created_at', '')
        }
