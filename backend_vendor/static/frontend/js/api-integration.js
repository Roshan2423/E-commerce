// API Integration for Django Backend
class APIClient {
    constructor() {
        // Use relative path for single server setup
        this.baseURL = window.API_BASE_URL || '';
        this.token = localStorage.getItem('authToken');
    }

    // Helper method for making API requests
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultHeaders = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            defaultHeaders['Authorization'] = `Bearer ${this.token}`;
        }

        const config = {
            headers: { ...defaultHeaders, ...options.headers },
            ...options,
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Authentication methods
    async login(credentials) {
        try {
            // Login with Django backend using username/password
            const response = await fetch(`${this.baseURL}/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: new URLSearchParams({
                    username: credentials.username,
                    password: credentials.password,
                }),
                credentials: 'include',
            });

            if (response.ok) {
                // Check if user is admin/staff by making a test request to dashboard
                const dashboardResponse = await fetch(`${this.baseURL}/dashboard/`, {
                    credentials: 'include',
                });
                
                if (dashboardResponse.ok) {
                    const user = {
                        username: credentials.username,
                        first_name: credentials.username,
                        is_staff: true,
                        is_superuser: true // Assume admin for demo
                    };
                    localStorage.setItem('currentUser', JSON.stringify(user));
                    return { user, success: true };
                }
            }
            
            throw new Error('Login failed');
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message };
        }
    }

    // Google OAuth Authentication
    async googleLogin(googleUser) {
        try {
            // Send Google ID token to Django backend for verification
            const response = await fetch(`${this.baseURL}/auth/google/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    id_token: googleUser.idToken,
                    email: googleUser.user.email,
                    name: googleUser.user.name,
                    picture: googleUser.user.picture
                }),
                credentials: 'include',
            });

            if (response.ok) {
                const data = await response.json();
                
                // Check if user has admin privileges
                const dashboardResponse = await fetch(`${this.baseURL}/dashboard/`, {
                    credentials: 'include',
                });
                
                const user = {
                    id: googleUser.user.id,
                    email: googleUser.user.email,
                    first_name: googleUser.user.givenName,
                    last_name: googleUser.user.familyName,
                    name: googleUser.user.name,
                    picture: googleUser.user.picture,
                    is_staff: dashboardResponse.ok,
                    is_superuser: dashboardResponse.ok,
                    login_method: 'google'
                };
                
                localStorage.setItem('currentUser', JSON.stringify(user));
                return { user, success: true };
            }
            
            throw new Error('Google authentication failed');
        } catch (error) {
            console.error('Google login error:', error);
            return { success: false, error: error.message };
        }
    }

    async logout() {
        try {
            // Try API logout endpoint first (which doesn't require CSRF for logout)
            await fetch(`${this.baseURL}/api/logout/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
            });
            
            localStorage.removeItem('currentUser');
            localStorage.removeItem('authToken');
            this.token = null;
            
            return { success: true };
        } catch (error) {
            // Even if logout fails on backend, clear local data
            console.error('Logout error:', error);
            localStorage.removeItem('currentUser');
            localStorage.removeItem('authToken');
            this.token = null;
            return { success: true }; // Still return success since local data is cleared
        }
    }

    // Get CSRF token from Django
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        return '';
    }

    // Product methods - Fetching from backend API
    async getProducts(filters = {}) {
        try {
            const response = await fetch(`${this.baseURL}/products/api/list/`);
            if (!response.ok) throw new Error('Failed to fetch products');
            const data = await response.json();
            if (data.success && data.products && data.products.length > 0) {
                console.log(`✅ Loaded ${data.products.length} real products from backend`);
                // Fix image URLs - prepend backend URL if they're relative paths
                const productsWithFixedImages = data.products.map(product => ({
                    ...product,
                    image: this.getFullImageURL(product.image)
                }));
                return productsWithFixedImages;
            }
            console.log('⚠️ No products in backend, using mock data');
            return this.getMockProducts();
        } catch (error) {
            console.error('Failed to fetch products:', error);
            console.log('⚠️ Using mock data as fallback');
            return this.getMockProducts();
        }
    }

    async getCategories() {
        try {
            const response = await fetch(`${this.baseURL}/products/api/categories/`);
            if (!response.ok) throw new Error('Failed to fetch categories');
            const data = await response.json();
            if (data.success && data.categories && data.categories.length > 0) {
                console.log(`✅ Loaded ${data.categories.length} real categories from backend`);
                // Fix image URLs - prepend backend URL if they're relative paths
                const categoriesWithFixedImages = data.categories.map(category => ({
                    ...category,
                    image: this.getFullImageURL(category.image)
                }));
                return categoriesWithFixedImages;
            }
            console.log('⚠️ No categories in backend, using mock data');
            return this.getMockCategories();
        } catch (error) {
            console.error('Failed to fetch categories:', error);
            console.log('⚠️ Using mock data as fallback');
            return this.getMockCategories();
        }
    }

    async getFlashSaleProducts() {
        try {
            const response = await fetch(`${this.baseURL}/products/api/flash-sale/`);
            if (!response.ok) throw new Error('Failed to fetch flash sale products');
            const data = await response.json();
            if (data.success && data.products) {
                console.log(`✅ Loaded ${data.products.length} flash sale products from backend`);
                const productsWithFixedImages = data.products.map(product => ({
                    ...product,
                    image: this.getFullImageURL(product.image)
                }));
                return productsWithFixedImages;
            }
            return [];
        } catch (error) {
            console.error('Failed to fetch flash sale products:', error);
            return [];
        }
    }

    async getSiteStats() {
        try {
            const response = await fetch(`${this.baseURL}/products/api/site-stats/`);
            if (!response.ok) throw new Error('Failed to fetch site stats');
            const data = await response.json();
            if (data.success && data.stats) {
                console.log(`✅ Loaded site stats from backend`);
                return data.stats;
            }
            return null;
        } catch (error) {
            console.error('Failed to fetch site stats:', error);
            return null;
        }
    }

    // Helper method to convert relative image URLs to absolute URLs
    getFullImageURL(imageUrl) {
        if (!imageUrl) {
            return 'https://via.placeholder.com/400x400/667eea/ffffff?text=No+Image';
        }
        
        // If it's already a full URL (starts with http:// or https://), return as is
        if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
            return imageUrl;
        }
        
        // If it's a relative path (starts with / or media/), prepend backend URL
        if (imageUrl.startsWith('/')) {
            return `${this.baseURL}${imageUrl}`;
        } else {
            return `${this.baseURL}/${imageUrl}`;
        }
    }

    // Mock data methods (will be replaced with real API calls)
    getMockProducts() {
        return [
            {
                id: 1,
                name: 'Wireless Headphones Pro',
                category: 'Electronics',
                price: 299.99,
                compare_price: 399.99,
                image: 'https://picsum.photos/400/400?random=1',
                rating: 4.8,
                reviews: 1247,
                stock_status: 'in_stock',
                description: 'Premium wireless headphones with noise cancellation and superior sound quality.',
                short_description: 'Professional grade wireless headphones'
            },
            {
                id: 2,
                name: 'Smart Fitness Watch',
                category: 'Electronics',
                price: 199.99,
                compare_price: 249.99,
                image: 'https://picsum.photos/400/400?random=2',
                rating: 4.6,
                reviews: 856,
                stock_status: 'in_stock',
                description: 'Advanced fitness tracking with heart rate monitoring and GPS.',
                short_description: 'Smart watch for fitness enthusiasts'
            },
            {
                id: 3,
                name: 'Designer Jacket',
                category: 'Fashion',
                price: 159.99,
                compare_price: null,
                image: 'https://picsum.photos/400/400?random=3',
                rating: 4.7,
                reviews: 423,
                stock_status: 'low_stock',
                description: 'Stylish designer jacket perfect for any season.',
                short_description: 'Premium designer outerwear'
            },
            {
                id: 4,
                name: 'Coffee Maker Deluxe',
                category: 'Home & Garden',
                price: 89.99,
                compare_price: 129.99,
                image: 'https://picsum.photos/400/400?random=4',
                rating: 4.5,
                reviews: 672,
                stock_status: 'in_stock',
                description: 'Professional coffee maker with programmable features.',
                short_description: 'Deluxe coffee brewing system'
            },
            {
                id: 5,
                name: 'Gaming Keyboard RGB',
                category: 'Electronics',
                price: 79.99,
                compare_price: 99.99,
                image: 'https://picsum.photos/400/400?random=5',
                rating: 4.4,
                reviews: 234,
                stock_status: 'in_stock',
                description: 'Mechanical gaming keyboard with customizable RGB lighting.',
                short_description: 'RGB mechanical gaming keyboard'
            },
            {
                id: 6,
                name: 'Yoga Mat Premium',
                category: 'Sports',
                price: 49.99,
                compare_price: null,
                image: 'https://picsum.photos/400/400?random=6',
                rating: 4.9,
                reviews: 789,
                stock_status: 'in_stock',
                description: 'Premium non-slip yoga mat made from eco-friendly materials.',
                short_description: 'Eco-friendly premium yoga mat'
            }
        ];
    }

    getMockCategories() {
        return [
            { 
                id: 1, 
                name: 'Electronics', 
                slug: 'electronics', 
                image: 'https://picsum.photos/300/200?random=10',
                description: 'Latest tech gadgets and electronics'
            },
            { 
                id: 2, 
                name: 'Fashion', 
                slug: 'fashion', 
                image: 'https://picsum.photos/300/200?random=11',
                description: 'Trendy clothing and accessories'
            },
            { 
                id: 3, 
                name: 'Home & Garden', 
                slug: 'home-garden', 
                image: 'https://picsum.photos/300/200?random=12',
                description: 'Everything for your home and garden'
            },
            { 
                id: 4, 
                name: 'Sports', 
                slug: 'sports', 
                image: 'https://picsum.photos/300/200?random=13',
                description: 'Sports equipment and fitness gear'
            },
            { 
                id: 5, 
                name: 'Books', 
                slug: 'books', 
                image: 'https://picsum.photos/300/200?random=14',
                description: 'Books, magazines, and educational materials'
            },
        ];
    }

    // Shopping cart methods
    async addToCart(productId, quantity = 1) {
        // Future API integration
        // return this.request('/api/cart/add/', {
        //     method: 'POST',
        //     body: JSON.stringify({ product_id: productId, quantity })
        // });
        
        // For now, handle locally
        return { success: true, message: 'Product added to cart' };
    }

    // Search functionality
    async searchProducts(query) {
        try {
            // Future: return this.request(`/api/products/search/?q=${encodeURIComponent(query)}`);
            const products = this.getMockProducts();
            return products.filter(product => 
                product.name.toLowerCase().includes(query.toLowerCase()) ||
                product.category.toLowerCase().includes(query.toLowerCase()) ||
                product.description.toLowerCase().includes(query.toLowerCase())
            );
        } catch (error) {
            console.error('Search failed:', error);
            return [];
        }
    }

    // Newsletter subscription
    async subscribeNewsletter(email) {
        try {
            // Future API integration
            console.log('Newsletter subscription:', email);
            return { success: true, message: 'Successfully subscribed to newsletter!' };
        } catch (error) {
            console.error('Newsletter subscription failed:', error);
            return { success: false, error: error.message };
        }
    }
}

// Export for use in main app
window.APIClient = APIClient;