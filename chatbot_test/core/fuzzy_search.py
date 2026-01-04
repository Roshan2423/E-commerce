"""
Fuzzy Product Search for OVN Store Chatbot
Handles typo-tolerant product search using difflib
"""
from difflib import SequenceMatcher, get_close_matches
from typing import List, Dict, Optional, Tuple
import re
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Search result with confidence score"""
    product: Dict
    score: float
    matched_field: str
    matched_text: str


class FuzzyProductSearch:
    """
    Typo-tolerant product search using fuzzy matching.
    Uses Python's built-in difflib for string similarity.
    """

    # Minimum similarity score to consider a match
    MIN_SCORE = 0.5

    # Field weights for scoring
    FIELD_WEIGHTS = {
        'name': 1.5,        # Product name most important
        'category': 1.2,    # Category somewhat important
        'description': 0.8  # Description less important
    }

    def __init__(self, products: List[Dict] = None):
        """
        Initialize search with product list.

        Args:
            products: List of product dictionaries
        """
        self._products = products or []
        self._name_index = {}
        self._build_index()

    def set_products(self, products: List[Dict]) -> None:
        """Set product list and rebuild index"""
        self._products = products
        self._build_index()

    def _build_index(self) -> None:
        """Build search index from products"""
        self._name_index = {}
        for product in self._products:
            name = product.get('name', '').lower()
            self._name_index[name] = product

    def _similarity_score(self, query: str, text: str) -> float:
        """
        Calculate similarity score between query and text.

        Args:
            query: Search query
            text: Text to compare

        Returns:
            Similarity score between 0 and 1
        """
        if not query or not text:
            return 0.0

        query = query.lower().strip()
        text = text.lower().strip()

        # Exact match
        if query == text:
            return 1.0

        # Contains match (partial)
        if query in text:
            return 0.9

        # Word-level matching
        query_words = set(query.split())
        text_words = set(text.split())

        # Check if any query words are in text
        common_words = query_words.intersection(text_words)
        if common_words:
            word_score = len(common_words) / len(query_words)
            return min(0.85, word_score)

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, query, text).ratio()

    def _tokenize(self, text: str) -> List[str]:
        """Split text into searchable tokens"""
        # Remove special characters and split
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return [w for w in text.split() if len(w) >= 2]

    def search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = None
    ) -> List[SearchResult]:
        """
        Search products with fuzzy matching.

        Args:
            query: Search query (can have typos)
            limit: Maximum results to return
            min_score: Minimum score threshold (default: MIN_SCORE)

        Returns:
            List of SearchResult objects sorted by score
        """
        if not query or not self._products:
            return []

        min_score = min_score or self.MIN_SCORE
        query = query.lower().strip()
        query_tokens = self._tokenize(query)

        results: List[SearchResult] = []
        seen_ids = set()

        for product in self._products:
            product_id = product.get('id') or product.get('_id')
            if product_id in seen_ids:
                continue

            # Search in different fields
            best_score = 0.0
            best_field = ''
            best_text = ''

            # Search product name
            name = product.get('name', '')
            name_score = self._similarity_score(query, name)
            name_score *= self.FIELD_WEIGHTS['name']
            if name_score > best_score:
                best_score = name_score
                best_field = 'name'
                best_text = name

            # Search category
            category = product.get('category', '') or product.get('category_name', '')
            if category:
                cat_score = self._similarity_score(query, category)
                cat_score *= self.FIELD_WEIGHTS['category']
                if cat_score > best_score:
                    best_score = cat_score
                    best_field = 'category'
                    best_text = category

            # Search description (if exists)
            description = product.get('description', '')
            if description:
                desc_score = self._similarity_score(query, description[:200])
                desc_score *= self.FIELD_WEIGHTS['description']
                if desc_score > best_score:
                    best_score = desc_score
                    best_field = 'description'
                    best_text = description[:100]

            # Token-based matching
            name_tokens = self._tokenize(name)
            for q_token in query_tokens:
                matches = get_close_matches(q_token, name_tokens, n=1, cutoff=0.7)
                if matches:
                    token_score = 0.7 * self.FIELD_WEIGHTS['name']
                    if token_score > best_score:
                        best_score = token_score
                        best_field = 'name_token'
                        best_text = name

            # Normalize score to 0-1 range
            best_score = min(1.0, best_score)

            if best_score >= min_score:
                seen_ids.add(product_id)
                results.append(SearchResult(
                    product=product,
                    score=best_score,
                    matched_field=best_field,
                    matched_text=best_text
                ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:limit]

    def search_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find products in a category (fuzzy match).

        Args:
            category: Category name
            limit: Maximum results

        Returns:
            List of products
        """
        category = category.lower().strip()
        results = []

        for product in self._products:
            prod_category = product.get('category', '') or product.get('category_name', '')
            if prod_category:
                score = self._similarity_score(category, prod_category)
                if score >= 0.7:
                    results.append((product, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in results[:limit]]

    def suggest_corrections(
        self,
        query: str,
        n: int = 3
    ) -> List[str]:
        """
        Suggest corrections for misspelled query.

        Args:
            query: Search query
            n: Number of suggestions

        Returns:
            List of suggested corrections
        """
        if not query:
            return []

        query = query.lower().strip()

        # Get all product names
        all_names = [p.get('name', '').lower() for p in self._products]

        # Find close matches
        suggestions = get_close_matches(query, all_names, n=n, cutoff=0.5)

        return suggestions

    def get_popular_products(self, limit: int = 5) -> List[Dict]:
        """
        Get popular/featured products.

        Args:
            limit: Maximum products

        Returns:
            List of products
        """
        # Sort by rating if available, otherwise by stock
        sorted_products = sorted(
            self._products,
            key=lambda p: (
                p.get('rating', 0) or 0,
                p.get('stock_quantity', 0) or 0
            ),
            reverse=True
        )
        return sorted_products[:limit]


class ProductSearchEngine:
    """
    Complete product search engine with fuzzy search and filters.
    """

    def __init__(self, api_client=None):
        """
        Initialize search engine.

        Args:
            api_client: Optional API client to fetch products
        """
        self.api_client = api_client
        self.fuzzy_search = FuzzyProductSearch()
        self._products_loaded = False

    def load_products(self) -> bool:
        """Load products from API"""
        if self.api_client:
            try:
                result = self.api_client.get_products()
                products = result.get('products', [])
                self.fuzzy_search.set_products(products)
                self._products_loaded = True
                return True
            except Exception as e:
                print(f"Error loading products: {e}")
                return False
        return False

    def search(
        self,
        query: str,
        category: str = None,
        min_price: float = None,
        max_price: float = None,
        in_stock_only: bool = False,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search products with filters.

        Args:
            query: Search query
            category: Filter by category
            min_price: Minimum price
            max_price: Maximum price
            in_stock_only: Only in-stock products
            limit: Maximum results

        Returns:
            List of matching products
        """
        if not self._products_loaded:
            self.load_products()

        # Get fuzzy matches
        results = self.fuzzy_search.search(query, limit=limit * 2)

        # Apply filters
        filtered = []
        for result in results:
            product = result.product

            # Category filter
            if category:
                prod_cat = product.get('category', '') or product.get('category_name', '')
                if category.lower() not in prod_cat.lower():
                    continue

            # Price filters
            price = product.get('price', 0) or 0
            if min_price and price < min_price:
                continue
            if max_price and price > max_price:
                continue

            # Stock filter
            if in_stock_only:
                stock = product.get('stock_quantity', 0) or 0
                if stock <= 0:
                    continue

            filtered.append(product)

            if len(filtered) >= limit:
                break

        return filtered

    def find_similar(
        self,
        product_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find products similar to given product.

        Args:
            product_id: Product ID to find similar to
            limit: Maximum results

        Returns:
            List of similar products
        """
        if not self._products_loaded:
            self.load_products()

        # Find the target product
        target = None
        for p in self.fuzzy_search._products:
            if p.get('id') == product_id or p.get('_id') == product_id:
                target = p
                break

        if not target:
            return []

        # Find products in same category
        category = target.get('category', '') or target.get('category_name', '')
        if category:
            similar = self.fuzzy_search.search_by_category(category, limit=limit + 1)
            # Remove the target product
            similar = [p for p in similar if p.get('id') != product_id]
            return similar[:limit]

        # Fallback to popular products
        return self.fuzzy_search.get_popular_products(limit)


# Global search engine instance
_search_engine: Optional[ProductSearchEngine] = None


def get_search_engine(api_client=None) -> ProductSearchEngine:
    """Get or create search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = ProductSearchEngine(api_client)
    return _search_engine


def fuzzy_search_products(
    query: str,
    products: List[Dict] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Convenience function for fuzzy product search.

    Args:
        query: Search query
        products: Optional product list (uses cached if not provided)
        limit: Maximum results

    Returns:
        List of matching products
    """
    if products:
        searcher = FuzzyProductSearch(products)
    else:
        searcher = get_search_engine().fuzzy_search

    results = searcher.search(query, limit=limit)
    return [r.product for r in results]
