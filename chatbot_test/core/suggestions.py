"""
Product Recommendations for OVN Store Chatbot
Generates "You might also like" suggestions
"""
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import random


@dataclass
class Recommendation:
    """Product recommendation with reason"""
    product: Dict
    score: float
    reason: str


class ProductRecommender:
    """
    Generates product recommendations based on various strategies:
    - Category-based: Same category products
    - Price-based: Similar price range
    - Popular: Best sellers / highest rated
    - Complementary: Products often bought together
    """

    # Price similarity tolerance (percentage)
    PRICE_TOLERANCE = 0.3  # 30%

    def __init__(self, api_client=None):
        """
        Initialize recommender.

        Args:
            api_client: Django API client for fetching products
        """
        self.api_client = api_client
        self._products_cache: List[Dict] = []
        self._categories_cache: Dict[str, List[Dict]] = {}

    def set_products(self, products: List[Dict]) -> None:
        """Set product cache"""
        self._products_cache = products
        self._build_category_index()

    def _build_category_index(self) -> None:
        """Build category to products index"""
        self._categories_cache = {}
        for product in self._products_cache:
            category = product.get('category', '') or product.get('category_name', 'Other')
            if category not in self._categories_cache:
                self._categories_cache[category] = []
            self._categories_cache[category].append(product)

    def _load_products(self) -> bool:
        """Load products from API if not cached"""
        if self._products_cache:
            return True

        if self.api_client:
            try:
                result = self.api_client.get_products()
                products = result.get('products', [])
                self.set_products(products)
                return True
            except Exception as e:
                print(f"Error loading products for recommendations: {e}")
                return False
        return False

    def get_suggestions_after_purchase(
        self,
        purchased_product: Dict,
        limit: int = 4,
        exclude_ids: Set = None
    ) -> List[Recommendation]:
        """
        Get product suggestions after a purchase.

        Args:
            purchased_product: The product that was purchased
            limit: Maximum suggestions
            exclude_ids: Product IDs to exclude

        Returns:
            List of Recommendation objects
        """
        self._load_products()

        exclude_ids = exclude_ids or set()
        purchased_id = purchased_product.get('id') or purchased_product.get('_id')
        if purchased_id:
            exclude_ids.add(purchased_id)

        recommendations = []

        # Strategy 1: Same category products (highest priority)
        category = purchased_product.get('category', '') or purchased_product.get('category_name', '')
        if category:
            category_products = self._get_category_products(category, exclude_ids)
            for product in category_products[:2]:
                recommendations.append(Recommendation(
                    product=product,
                    score=0.9,
                    reason=f"From {category} collection"
                ))

        # Strategy 2: Similar price range
        price = purchased_product.get('price', 0) or 0
        if price > 0:
            similar_price = self._get_similar_price_products(price, exclude_ids)
            for product in similar_price[:2]:
                if len(recommendations) < limit:
                    recommendations.append(Recommendation(
                        product=product,
                        score=0.7,
                        reason="Similar price range"
                    ))

        # Strategy 3: Popular products (fill remaining slots)
        if len(recommendations) < limit:
            popular = self._get_popular_products(exclude_ids)
            for product in popular:
                if len(recommendations) >= limit:
                    break
                # Check if already in recommendations
                rec_ids = {r.product.get('id') or r.product.get('_id') for r in recommendations}
                prod_id = product.get('id') or product.get('_id')
                if prod_id not in rec_ids:
                    recommendations.append(Recommendation(
                        product=product,
                        score=0.5,
                        reason="Popular choice"
                    ))

        return recommendations[:limit]

    def get_category_recommendations(
        self,
        category: str,
        limit: int = 4,
        exclude_ids: Set = None
    ) -> List[Recommendation]:
        """
        Get recommendations from a specific category.

        Args:
            category: Category name
            limit: Maximum suggestions
            exclude_ids: Product IDs to exclude

        Returns:
            List of Recommendation objects
        """
        self._load_products()

        exclude_ids = exclude_ids or set()
        products = self._get_category_products(category, exclude_ids)

        recommendations = []
        for product in products[:limit]:
            recommendations.append(Recommendation(
                product=product,
                score=0.8,
                reason=f"{category} products"
            ))

        return recommendations

    def get_popular_recommendations(
        self,
        limit: int = 4,
        exclude_ids: Set = None
    ) -> List[Recommendation]:
        """
        Get popular product recommendations.

        Args:
            limit: Maximum suggestions
            exclude_ids: Product IDs to exclude

        Returns:
            List of Recommendation objects
        """
        self._load_products()

        exclude_ids = exclude_ids or set()
        popular = self._get_popular_products(exclude_ids)

        recommendations = []
        for product in popular[:limit]:
            recommendations.append(Recommendation(
                product=product,
                score=0.6,
                reason="Popular item"
            ))

        return recommendations

    def get_flash_sale_recommendations(
        self,
        limit: int = 4
    ) -> List[Recommendation]:
        """
        Get flash sale product recommendations.

        Args:
            limit: Maximum suggestions

        Returns:
            List of Recommendation objects
        """
        self._load_products()

        flash_sale = [
            p for p in self._products_cache
            if p.get('is_flash_sale', False)
        ]

        # Sort by discount percentage
        flash_sale.sort(
            key=lambda p: self._calculate_discount(p),
            reverse=True
        )

        recommendations = []
        for product in flash_sale[:limit]:
            discount = self._calculate_discount(product)
            recommendations.append(Recommendation(
                product=product,
                score=0.95,
                reason=f"{int(discount)}% off - Flash Sale!"
            ))

        return recommendations

    def _get_category_products(
        self,
        category: str,
        exclude_ids: Set
    ) -> List[Dict]:
        """Get products from category excluding specified IDs"""
        category_lower = category.lower()

        # Try exact match first
        for cat, products in self._categories_cache.items():
            if cat.lower() == category_lower:
                return [
                    p for p in products
                    if (p.get('id') or p.get('_id')) not in exclude_ids
                ]

        # Try partial match
        for cat, products in self._categories_cache.items():
            if category_lower in cat.lower() or cat.lower() in category_lower:
                return [
                    p for p in products
                    if (p.get('id') or p.get('_id')) not in exclude_ids
                ]

        return []

    def _get_similar_price_products(
        self,
        target_price: float,
        exclude_ids: Set
    ) -> List[Dict]:
        """Get products in similar price range"""
        min_price = target_price * (1 - self.PRICE_TOLERANCE)
        max_price = target_price * (1 + self.PRICE_TOLERANCE)

        matching = [
            p for p in self._products_cache
            if (p.get('id') or p.get('_id')) not in exclude_ids
            and min_price <= (p.get('price', 0) or 0) <= max_price
        ]

        # Sort by rating
        matching.sort(key=lambda p: p.get('rating', 0) or 0, reverse=True)

        return matching

    def _get_popular_products(self, exclude_ids: Set) -> List[Dict]:
        """Get popular products based on rating and stock"""
        products = [
            p for p in self._products_cache
            if (p.get('id') or p.get('_id')) not in exclude_ids
            and (p.get('stock_quantity', 0) or 0) > 0
        ]

        # Sort by rating, then by reviews count
        products.sort(
            key=lambda p: (
                p.get('rating', 0) or 0,
                p.get('reviews', 0) or 0
            ),
            reverse=True
        )

        return products

    def _calculate_discount(self, product: Dict) -> float:
        """Calculate discount percentage for a product"""
        price = product.get('price', 0) or 0
        compare_price = product.get('compare_price', 0) or 0
        flash_sale_price = product.get('flash_sale_price', 0) or 0

        if flash_sale_price and price > flash_sale_price:
            return ((price - flash_sale_price) / price) * 100

        if compare_price and compare_price > price:
            return ((compare_price - price) / compare_price) * 100

        return 0

    def format_suggestions_message(
        self,
        recommendations: List[Recommendation],
        intro_text: str = None
    ) -> str:
        """
        Format recommendations as chat message.

        Args:
            recommendations: List of recommendations
            intro_text: Optional intro text

        Returns:
            Formatted message string
        """
        if not recommendations:
            return ""

        intro_options = [
            "You might also like:",
            "Customers also bought:",
            "Related products you may like:",
            "Check out these too:"
        ]

        message = intro_text or random.choice(intro_options)
        message += "\n"

        for i, rec in enumerate(recommendations, 1):
            product = rec.product
            name = product.get('name', 'Product')[:40]
            price = product.get('price', 0) or 0

            # Check for sale price
            flash_price = product.get('flash_sale_price')
            if flash_price and product.get('is_flash_sale'):
                message += f"\n{i}. **{name}**\n   ~~Rs. {price:,.0f}~~ **Rs. {flash_price:,.0f}** ({rec.reason})"
            else:
                message += f"\n{i}. **{name}** - Rs. {price:,.0f}\n   ({rec.reason})"

        return message


# Global recommender instance
_recommender: Optional[ProductRecommender] = None


def get_recommender(api_client=None) -> ProductRecommender:
    """Get or create recommender instance"""
    global _recommender
    if _recommender is None:
        _recommender = ProductRecommender(api_client)
    elif api_client and not _recommender.api_client:
        _recommender.api_client = api_client
    return _recommender


def get_suggestions_after_purchase(
    purchased_product: Dict,
    api_client=None,
    limit: int = 4
) -> List[Dict]:
    """
    Convenience function to get suggestions after purchase.

    Args:
        purchased_product: The purchased product
        api_client: Optional API client
        limit: Maximum suggestions

    Returns:
        List of suggested products
    """
    recommender = get_recommender(api_client)
    recommendations = recommender.get_suggestions_after_purchase(purchased_product, limit)
    return [r.product for r in recommendations]


def format_suggestions(
    purchased_product: Dict,
    api_client=None,
    limit: int = 4
) -> str:
    """
    Convenience function to get formatted suggestions message.

    Args:
        purchased_product: The purchased product
        api_client: Optional API client
        limit: Maximum suggestions

    Returns:
        Formatted message string
    """
    recommender = get_recommender(api_client)
    recommendations = recommender.get_suggestions_after_purchase(purchased_product, limit)
    return recommender.format_suggestions_message(recommendations)
