// E-Commerce Frontend Application - Revolutionary Design

// ============================================
// FAST SEARCH ENGINE - Trie + Fuzzy Search
// ============================================

// Trie Node for fast prefix matching
class TrieNode {
    constructor() {
        this.children = {};
        this.isEndOfWord = false;
        this.products = []; // Products that match this prefix
    }
}

// Trie data structure for O(m) prefix search where m is query length
class Trie {
    constructor() {
        this.root = new TrieNode();
    }

    // Insert a word with associated product
    insert(word, product) {
        let node = this.root;
        const lowerWord = word.toLowerCase();

        for (const char of lowerWord) {
            if (!node.children[char]) {
                node.children[char] = new TrieNode();
            }
            node = node.children[char];
            // Add product to every prefix node for instant results
            if (!node.products.find(p => p.id === product.id)) {
                node.products.push(product);
            }
        }
        node.isEndOfWord = true;
    }

    // Search for products matching prefix - O(m) time complexity
    search(prefix) {
        let node = this.root;
        const lowerPrefix = prefix.toLowerCase();

        for (const char of lowerPrefix) {
            if (!node.children[char]) {
                return [];
            }
            node = node.children[char];
        }
        return node.products;
    }
}

// Fast Search Engine combining Trie + Fuzzy matching
class SearchEngine {
    constructor() {
        this.trie = new Trie();
        this.products = [];
        this.searchIndex = new Map(); // Inverted index for fast lookups
    }

    // Build search index from products
    buildIndex(products) {
        this.products = products;
        this.trie = new Trie();
        this.searchIndex.clear();

        products.forEach(product => {
            // Index product name words
            const nameWords = product.name.toLowerCase().split(/\s+/);
            nameWords.forEach(word => {
                this.trie.insert(word, product);
                this.addToIndex(word, product);
            });

            // Index full name for phrase matching
            this.trie.insert(product.name, product);

            // Index category
            if (product.category) {
                this.trie.insert(product.category, product);
                this.addToIndex(product.category.toLowerCase(), product);
            }

            // Index SKU
            if (product.sku) {
                this.trie.insert(product.sku, product);
            }
        });
    }

    // Add to inverted index
    addToIndex(term, product) {
        if (!this.searchIndex.has(term)) {
            this.searchIndex.set(term, new Set());
        }
        this.searchIndex.get(term).add(product.id);
    }

    // Levenshtein distance for fuzzy matching - O(m*n)
    levenshteinDistance(str1, str2) {
        const m = str1.length;
        const n = str2.length;

        // Use single row optimization for space O(n)
        let prev = Array(n + 1).fill(0).map((_, i) => i);
        let curr = Array(n + 1).fill(0);

        for (let i = 1; i <= m; i++) {
            curr[0] = i;
            for (let j = 1; j <= n; j++) {
                if (str1[i - 1] === str2[j - 1]) {
                    curr[j] = prev[j - 1];
                } else {
                    curr[j] = 1 + Math.min(prev[j - 1], prev[j], curr[j - 1]);
                }
            }
            [prev, curr] = [curr, prev];
        }
        return prev[n];
    }

    // Calculate relevance score for ranking results
    calculateScore(product, query) {
        const lowerQuery = query.toLowerCase();
        const lowerName = product.name.toLowerCase();
        const lowerCategory = (product.category || '').toLowerCase();

        let score = 0;

        // Exact match bonus (highest priority)
        if (lowerName === lowerQuery) score += 100;

        // Starts with query (high priority)
        if (lowerName.startsWith(lowerQuery)) score += 50;

        // Contains exact query
        if (lowerName.includes(lowerQuery)) score += 30;

        // Word match bonus
        const queryWords = lowerQuery.split(/\s+/);
        const nameWords = lowerName.split(/\s+/);

        queryWords.forEach(qWord => {
            nameWords.forEach(nWord => {
                if (nWord === qWord) score += 20;
                else if (nWord.startsWith(qWord)) score += 10;
            });
        });

        // Category match
        if (lowerCategory.includes(lowerQuery)) score += 15;

        // Fuzzy match score (for typo tolerance)
        const minDistance = Math.min(
            ...nameWords.map(word => this.levenshteinDistance(lowerQuery, word))
        );
        if (minDistance <= 2) {
            score += (3 - minDistance) * 5; // Lower distance = higher score
        }

        return score;
    }

    // Main search function - combines Trie prefix search + fuzzy matching
    search(query, limit = 10) {
        if (!query || query.trim().length === 0) {
            return [];
        }

        const trimmedQuery = query.trim();
        const results = new Map(); // Use Map to deduplicate

        // 1. Trie prefix search - O(m) where m is query length
        const trieResults = this.trie.search(trimmedQuery);
        trieResults.forEach(product => {
            results.set(product.id, product);
        });

        // 2. If few results, add fuzzy matches
        if (results.size < limit) {
            const queryLower = trimmedQuery.toLowerCase();

            this.products.forEach(product => {
                if (results.has(product.id)) return;

                const nameLower = product.name.toLowerCase();
                const categoryLower = (product.category || '').toLowerCase();

                // Check if any word in name is close to query (fuzzy)
                const nameWords = nameLower.split(/\s+/);
                const isFuzzyMatch = nameWords.some(word => {
                    const distance = this.levenshteinDistance(queryLower, word);
                    return distance <= Math.max(1, Math.floor(queryLower.length / 3));
                });

                // Also check partial matches
                const isPartialMatch = nameLower.includes(queryLower) ||
                                       categoryLower.includes(queryLower);

                if (isFuzzyMatch || isPartialMatch) {
                    results.set(product.id, product);
                }
            });
        }

        // 3. Score and sort results
        const scoredResults = Array.from(results.values()).map(product => ({
            ...product,
            searchScore: this.calculateScore(product, trimmedQuery)
        }));

        // Sort by score descending, then by name
        scoredResults.sort((a, b) => {
            if (b.searchScore !== a.searchScore) {
                return b.searchScore - a.searchScore;
            }
            return a.name.localeCompare(b.name);
        });

        return scoredResults.slice(0, limit);
    }
}

// Debounce utility for search performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Global search engine instance
const searchEngine = new SearchEngine();

// Nepal District Delivery Rates (Rate per 0.5 Kg)
const NEPAL_DELIVERY_RATES = [
    {"district": "Achham", "location": "Achhamsanfebagar", "rate": 285},
    {"district": "Achham", "location": "Kamalbazar", "rate": 290},
    {"district": "Achham", "location": "Mangalsen", "rate": 285},
    {"district": "Arghakhanchi", "location": "Sandhikarka", "rate": 215},
    {"district": "Baglung", "location": "Baglung", "rate": 180},
    {"district": "Baglung", "location": "Burtibang", "rate": 240},
    {"district": "Baglung", "location": "Galkot", "rate": 205},
    {"district": "Baitadi", "location": "Gothalapani", "rate": 290},
    {"district": "Baitadi", "location": "Patan", "rate": 290},
    {"district": "Bajhang", "location": "Chainpur", "rate": 290},
    {"district": "Bajura", "location": "Kolti", "rate": 290},
    {"district": "Bajura", "location": "Martadi", "rate": 290},
    {"district": "Banke", "location": "Khajura", "rate": 200},
    {"district": "Banke", "location": "Kohalpur", "rate": 170},
    {"district": "Banke", "location": "Nepalgunj", "rate": 170},
    {"district": "Banke", "location": "Samshergunj", "rate": 220},
    {"district": "Bara", "location": "Amlekhgunj", "rate": 190},
    {"district": "Bara", "location": "Jeetpur", "rate": 190},
    {"district": "Bara", "location": "Kalaiya", "rate": 190},
    {"district": "Bara", "location": "Kolhabibazar", "rate": 200},
    {"district": "Bara", "location": "Nijgadh", "rate": 190},
    {"district": "Bara", "location": "Pathlaiya", "rate": 190},
    {"district": "Bara", "location": "Simara", "rate": 190},
    {"district": "Bardiya", "location": "Bansagadhi", "rate": 240},
    {"district": "Bardiya", "location": "Bhurigaun", "rate": 215},
    {"district": "Bardiya", "location": "Gulariya", "rate": 215},
    {"district": "Bardiya", "location": "Jayanagar", "rate": 240},
    {"district": "Bardiya", "location": "Mainapokhari", "rate": 240},
    {"district": "Bardiya", "location": "Rajapur", "rate": 215},
    {"district": "Bardiya", "location": "Taratal", "rate": 240},
    {"district": "Bhaktapur", "location": "Bhaktapur", "rate": 100},
    {"district": "Bhaktapur", "location": "Nagarkot", "rate": 190},
    {"district": "Bhojpur", "location": "Bhojpur", "rate": 265},
    {"district": "Bhojpur", "location": "Dingla", "rate": 290},
    {"district": "Chitwan", "location": "Bhandara", "rate": 225},
    {"district": "Chitwan", "location": "Bharatpur", "rate": 145},
    {"district": "Chitwan", "location": "Chanauli", "rate": 200},
    {"district": "Chitwan", "location": "Dasdhunga", "rate": 240},
    {"district": "Chitwan", "location": "Gaidakot", "rate": 165},
    {"district": "Chitwan", "location": "Jagatpur", "rate": 200},
    {"district": "Chitwan", "location": "Jugedi", "rate": 190},
    {"district": "Chitwan", "location": "Lothar", "rate": 200},
    {"district": "Chitwan", "location": "Madi", "rate": 200},
    {"district": "Chitwan", "location": "Meghauli", "rate": 240},
    {"district": "Chitwan", "location": "Narayangarh", "rate": 135},
    {"district": "Chitwan", "location": "Padampur", "rate": 195},
    {"district": "Chitwan", "location": "Parsa", "rate": 190},
    {"district": "Chitwan", "location": "Sauraha", "rate": 215},
    {"district": "Chitwan", "location": "Tandi", "rate": 160},
    {"district": "Dadeldhura", "location": "Amargadhi", "rate": 265},
    {"district": "Dailekh", "location": "Dailekhbazar", "rate": 240},
    {"district": "Dailekh", "location": "Dullu", "rate": 290},
    {"district": "Dang", "location": "Bhalubang", "rate": 190},
    {"district": "Dang", "location": "Ghorahi", "rate": 180},
    {"district": "Dang", "location": "Gogali", "rate": 200},
    {"district": "Dang", "location": "Lamahi", "rate": 190},
    {"district": "Dang", "location": "Mourighat", "rate": 190},
    {"district": "Dang", "location": "Narayanpur", "rate": 200},
    {"district": "Dang", "location": "Tulsipur", "rate": 180},
    {"district": "Darchula", "location": "Darchulakhalanga", "rate": 290},
    {"district": "Darchula", "location": "Gokuleshwor", "rate": 290},
    {"district": "Dhading", "location": "Dhadingbesi", "rate": 190},
    {"district": "Dhading", "location": "Gajuri", "rate": 235},
    {"district": "Dhading", "location": "Galchi", "rate": 240},
    {"district": "Dhading", "location": "Malekhu", "rate": 215},
    {"district": "Dhading", "location": "Naubise", "rate": 240},
    {"district": "Dhankuta", "location": "Dhankuta", "rate": 200},
    {"district": "Dhankuta", "location": "Hile", "rate": 230},
    {"district": "Dhankuta", "location": "Pakhribas", "rate": 210},
    {"district": "Dhankuta", "location": "Rajarani", "rate": 200},
    {"district": "Dhankuta", "location": "Sidhuwa", "rate": 290},
    {"district": "Dhanusa", "location": "Birendrabazar", "rate": 195},
    {"district": "Dhanusa", "location": "Dhanusadham", "rate": 195},
    {"district": "Dhanusa", "location": "Jaleshwor", "rate": 195},
    {"district": "Dhanusa", "location": "Janakpur", "rate": 180},
    {"district": "Dhanusa", "location": "Mahendranagar", "rate": 200},
    {"district": "Dhanusa", "location": "Nagarain", "rate": 195},
    {"district": "Dhanusa", "location": "Sabaila", "rate": 195},
    {"district": "Dhanusa", "location": "Tinkoriya", "rate": 195},
    {"district": "Dhanusa", "location": "Yadukuha", "rate": 195},
    {"district": "Dolakha", "location": "Dolakhacharikot", "rate": 195},
    {"district": "Dolakha", "location": "Jiri", "rate": 230},
    {"district": "Dolpa", "location": "Dunai", "rate": 290},
    {"district": "Doti", "location": "Budor", "rate": 290},
    {"district": "Doti", "location": "Dipayalbazar", "rate": 265},
    {"district": "Doti", "location": "Silgadhi", "rate": 265},
    {"district": "Gorkha", "location": "Gorkha", "rate": 190},
    {"district": "Gorkha", "location": "Palungtar", "rate": 225},
    {"district": "Gulmi", "location": "Baletaxar", "rate": 200},
    {"district": "Gulmi", "location": "Gulmi", "rate": 200},
    {"district": "Gulmi", "location": "Ridi", "rate": 210},
    {"district": "Gulmi", "location": "Shantipur", "rate": 210},
    {"district": "Gulmi", "location": "Tamghas", "rate": 200},
    {"district": "Humla", "location": "Simikot", "rate": 290},
    {"district": "Ilam", "location": "Chulachuli", "rate": 200},
    {"district": "Ilam", "location": "Fikkal", "rate": 210},
    {"district": "Ilam", "location": "Ilam", "rate": 190},
    {"district": "Ilam", "location": "Nepaltar", "rate": 195},
    {"district": "Ilam", "location": "Mangalbare", "rate": 200},
    {"district": "Ilam", "location": "Pashupatinagar", "rate": 240},
    {"district": "Ilam", "location": "Ranke", "rate": 200},
    {"district": "Ilam", "location": "Shreeantu", "rate": 200},
    {"district": "Jajarkot", "location": "Jajarkot", "rate": 290},
    {"district": "Jhapa", "location": "Bahundangi", "rate": 240},
    {"district": "Jhapa", "location": "Baniyani", "rate": 190},
    {"district": "Jhapa", "location": "Beldangi", "rate": 190},
    {"district": "Jhapa", "location": "Bhadrapur", "rate": 170},
    {"district": "Jhapa", "location": "Birtamod", "rate": 170},
    {"district": "Jhapa", "location": "Budhabare", "rate": 180},
    {"district": "Jhapa", "location": "Chandragadhi", "rate": 180},
    {"district": "Jhapa", "location": "Charali", "rate": 180},
    {"district": "Jhapa", "location": "Damak", "rate": 170},
    {"district": "Jhapa", "location": "Dhulabari", "rate": 180},
    {"district": "Jhapa", "location": "Garamani", "rate": 200},
    {"district": "Jhapa", "location": "Gauradaha", "rate": 190},
    {"district": "Jhapa", "location": "Gaurigunj", "rate": 180},
    {"district": "Jhapa", "location": "Goldhap", "rate": 195},
    {"district": "Jhapa", "location": "Haldibari", "rate": 180},
    {"district": "Jhapa", "location": "Jhiljhile", "rate": 190},
    {"district": "Jhapa", "location": "Kakarvitta", "rate": 180},
    {"district": "Jhapa", "location": "Kechana", "rate": 190},
    {"district": "Jhapa", "location": "Kerkha", "rate": 200},
    {"district": "Jhapa", "location": "Khudunabari", "rate": 215},
    {"district": "Jhapa", "location": "Laxmipur", "rate": 190},
    {"district": "Jhapa", "location": "Madhumalla", "rate": 190},
    {"district": "Jhapa", "location": "Pathari", "rate": 190},
    {"district": "Jhapa", "location": "Rajgadh", "rate": 215},
    {"district": "Jhapa", "location": "Ratuwamaisombare", "rate": 190},
    {"district": "Jhapa", "location": "Sanischare", "rate": 190},
    {"district": "Jhapa", "location": "Sharanmati", "rate": 200},
    {"district": "Jhapa", "location": "Shivagunj", "rate": 200},
    {"district": "Jhapa", "location": "Surunga", "rate": 190},
    {"district": "Jhapa", "location": "Urlabari", "rate": 175},
    {"district": "Jumla", "location": "Jumla", "rate": 290},
    {"district": "Jumla", "location": "Jumlakhalanga", "rate": 290},
    {"district": "Kailali", "location": "Attariya", "rate": 190},
    {"district": "Kailali", "location": "Bauniya", "rate": 215},
    {"district": "Kailali", "location": "Bhajani", "rate": 215},
    {"district": "Kailali", "location": "Chaumala", "rate": 240},
    {"district": "Kailali", "location": "Chisapani", "rate": 215},
    {"district": "Kailali", "location": "Dhangadhi", "rate": 180},
    {"district": "Kailali", "location": "Geta", "rate": 240},
    {"district": "Kailali", "location": "Godawari", "rate": 215},
    {"district": "Kailali", "location": "Hasuliya", "rate": 215},
    {"district": "Kailali", "location": "Joshipur", "rate": 240},
    {"district": "Kailali", "location": "Jugeda", "rate": 240},
    {"district": "Kailali", "location": "Lamki", "rate": 210},
    {"district": "Kailali", "location": "Masuriya", "rate": 240},
    {"district": "Kailali", "location": "Musikot", "rate": 265},
    {"district": "Kailali", "location": "Pahalbanpur", "rate": 215},
    {"district": "Kailali", "location": "Phulbari", "rate": 240},
    {"district": "Kailali", "location": "Sattibazar", "rate": 240},
    {"district": "Kailali", "location": "Sukkhad", "rate": 215},
    {"district": "Kailali", "location": "Tikapur", "rate": 215},
    {"district": "Kalikot", "location": "Manma", "rate": 290},
    {"district": "Kanchanpur", "location": "Belauri", "rate": 250},
    {"district": "Kanchanpur", "location": "Beldandi", "rate": 200},
    {"district": "Kanchanpur", "location": "Brahmadevbazar", "rate": 190},
    {"district": "Kanchanpur", "location": "Dodhara", "rate": 200},
    {"district": "Kanchanpur", "location": "Gulariya", "rate": 190},
    {"district": "Kanchanpur", "location": "Jhalari", "rate": 200},
    {"district": "Kanchanpur", "location": "Mahendranagar", "rate": 200},
    {"district": "Kanchanpur", "location": "Punarbas", "rate": 190},
    {"district": "Kapilvastu", "location": "Chandrauta", "rate": 200},
    {"district": "Kapilvastu", "location": "Gorusinge", "rate": 190},
    {"district": "Kapilvastu", "location": "Imiliya", "rate": 200},
    {"district": "Kapilvastu", "location": "Jeetpur", "rate": 200},
    {"district": "Kapilvastu", "location": "Kapilbastu", "rate": 200},
    {"district": "Kapilvastu", "location": "Krishnanagar", "rate": 210},
    {"district": "Kapilvastu", "location": "Maharajganj", "rate": 200},
    {"district": "Kapilvastu", "location": "Odari", "rate": 200},
    {"district": "Kapilvastu", "location": "Rudrapurharaiya", "rate": 200},
    {"district": "Kapilvastu", "location": "Taulihawa", "rate": 190},
    {"district": "Kaski", "location": "Hemja", "rate": 190},
    {"district": "Kaski", "location": "Naudanda", "rate": 190},
    {"district": "Kaski", "location": "Lekhnath", "rate": 145},
    {"district": "Kaski", "location": "Pokhara", "rate": 135},
    {"district": "Kathmandu", "location": "Dakshinkali", "rate": 150},
    {"district": "Kathmandu", "location": "Dolalghat", "rate": 240},
    {"district": "Kathmandu", "location": "Godawari", "rate": 100},
    {"district": "Kathmandu", "location": "Kathmandu", "rate": 100},
    {"district": "Kathmandu", "location": "Kirtipur", "rate": 100},
    {"district": "Kathmandu", "location": "Lele", "rate": 100},
    {"district": "Kathmandu", "location": "Lubhu/Lamatar", "rate": 100},
    {"district": "Kathmandu", "location": "Pharphing", "rate": 100},
    {"district": "Kathmandu", "location": "Sankhu", "rate": 150},
    {"district": "Kathmandu", "location": "Sundarijal", "rate": 150},
    {"district": "Kathmandu", "location": "Thankot", "rate": 150},
    {"district": "Kavrepalanchok", "location": "Banepa", "rate": 150},
    {"district": "Kavrepalanchok", "location": "Bhakundebesi", "rate": 215},
    {"district": "Kavrepalanchok", "location": "Dhulikhel", "rate": 150},
    {"district": "Kavrepalanchok", "location": "Kavre", "rate": 150},
    {"district": "Kavrepalanchok", "location": "Panauti", "rate": 150},
    {"district": "Kavrepalanchok", "location": "Panchkhal", "rate": 215},
    {"district": "Khotang", "location": "Diktel", "rate": 290},
    {"district": "Khotang", "location": "Khotang", "rate": 290},
    {"district": "Lalitpur", "location": "Lalitpur", "rate": 100},
    {"district": "Lamjung", "location": "Besisahar", "rate": 190},
    {"district": "Lamjung", "location": "Sundarbazar", "rate": 190},
    {"district": "Mahottari", "location": "Aurahi", "rate": 195},
    {"district": "Mahottari", "location": "Bardibas", "rate": 180},
    {"district": "Mahottari", "location": "Dhalkebar", "rate": 180},
    {"district": "Mahottari", "location": "Gaushala", "rate": 195},
    {"district": "Mahottari", "location": "Ramgopalpur", "rate": 195},
    {"district": "Mahottari", "location": "Samsi", "rate": 195},
    {"district": "Mahottari", "location": "Tuteshwar", "rate": 200},
    {"district": "Makwanpur", "location": "Daman", "rate": 240},
    {"district": "Makwanpur", "location": "Hetauda", "rate": 150},
    {"district": "Makwanpur", "location": "Manahari", "rate": 240},
    {"district": "Makwanpur", "location": "Padampokhari", "rate": 190},
    {"district": "Manang", "location": "Chame", "rate": 290},
    {"district": "Morang", "location": "Belbari", "rate": 180},
    {"district": "Morang", "location": "Biratchowk", "rate": 170},
    {"district": "Morang", "location": "Biratnagar", "rate": 140},
    {"district": "Morang", "location": "Kanepokhari", "rate": 190},
    {"district": "Morang", "location": "Kerabari", "rate": 200},
    {"district": "Morang", "location": "Letang", "rate": 190},
    {"district": "Morang", "location": "Ramailo", "rate": 190},
    {"district": "Morang", "location": "Rangeli", "rate": 190},
    {"district": "Mugu", "location": "Gamgadhi", "rate": 290},
    {"district": "Mustang", "location": "Jomsom", "rate": 290},
    {"district": "Myagdi", "location": "Beni", "rate": 180},
    {"district": "Myagdi", "location": "Darwang", "rate": 290},
    {"district": "Nawalparasi", "location": "Arunkhola", "rate": 190},
    {"district": "Nawalparasi", "location": "Bardaghat", "rate": 180},
    {"district": "Nawalparasi", "location": "Chormara", "rate": 180},
    {"district": "Nawalparasi", "location": "Daldale", "rate": 180},
    {"district": "Nawalparasi", "location": "Dumkibas", "rate": 180},
    {"district": "Nawalparasi", "location": "Gopigunj", "rate": 190},
    {"district": "Nawalparasi", "location": "Harkapur", "rate": 200},
    {"district": "Nawalparasi", "location": "Kawasoti", "rate": 180},
    {"district": "Nawalparasi", "location": "Khaireni", "rate": 190},
    {"district": "Nawalparasi", "location": "Parasiramgram", "rate": 200},
    {"district": "Nawalparasi", "location": "Rajahar", "rate": 190},
    {"district": "Nawalparasi", "location": "Sunwal", "rate": 175},
    {"district": "Nuwakot", "location": "Battar", "rate": 190},
    {"district": "Nuwakot", "location": "Bidur", "rate": 190},
    {"district": "Nuwakot", "location": "Trishuli", "rate": 200},
    {"district": "Okhaldhunga", "location": "Okhaldhunga", "rate": 290},
    {"district": "Palpa", "location": "Palpa", "rate": 195},
    {"district": "Palpa", "location": "Rampur", "rate": 190},
    {"district": "Palpa", "location": "Tansen", "rate": 180},
    {"district": "Panchthar", "location": "Jorpokhari", "rate": 200},
    {"district": "Panchthar", "location": "Phidim", "rate": 210},
    {"district": "Parbat", "location": "Kushma", "rate": 190},
    {"district": "Parbat", "location": "Nayapul", "rate": 230},
    {"district": "Parsa", "location": "Birgunj", "rate": 160},
    {"district": "Parsa", "location": "Pokhariya", "rate": 200},
    {"district": "Pyuthan", "location": "Bhingri", "rate": 265},
    {"district": "Pyuthan", "location": "Pyuthan", "rate": 240},
    {"district": "Pyuthan", "location": "Pyuthankhalanga", "rate": 265},
    {"district": "Ramechhap", "location": "Manthali", "rate": 195},
    {"district": "Rasuwa", "location": "Dhunche", "rate": 265},
    {"district": "Rautahat", "location": "Chandranigapur", "rate": 215},
    {"district": "Rautahat", "location": "Damarchowk", "rate": 215},
    {"district": "Rautahat", "location": "Garuda", "rate": 265},
    {"district": "Rautahat", "location": "Gaur", "rate": 190},
    {"district": "Rautahat", "location": "Rajdevi", "rate": 215},
    {"district": "Rolpa", "location": "Liwang", "rate": 240},
    {"district": "Rolpa", "location": "Sulichaur", "rate": 240},
    {"district": "Rukum", "location": "Chaurjahari", "rate": 290},
    {"district": "Rukum", "location": "Rukumkot", "rate": 290},
    {"district": "Rupandehi", "location": "Amuwa", "rate": 240},
    {"district": "Rupandehi", "location": "Bhairahawa", "rate": 140},
    {"district": "Rupandehi", "location": "Bhalwari", "rate": 190},
    {"district": "Rupandehi", "location": "Butwal", "rate": 140},
    {"district": "Rupandehi", "location": "Dhakdai", "rate": 200},
    {"district": "Rupandehi", "location": "Jogikuti", "rate": 160},
    {"district": "Rupandehi", "location": "KanchiBazar", "rate": 200},
    {"district": "Rupandehi", "location": "Kotihawa", "rate": 195},
    {"district": "Rupandehi", "location": "Lumbinibazar", "rate": 195},
    {"district": "Rupandehi", "location": "Manigram", "rate": 175},
    {"district": "Rupandehi", "location": "Motipur", "rate": 190},
    {"district": "Rupandehi", "location": "Murgiya", "rate": 190},
    {"district": "Rupandehi", "location": "Pharsatikar", "rate": 200},
    {"district": "Rupandehi", "location": "Tamnagar", "rate": 175},
    {"district": "Rupandehi", "location": "Thutipipal", "rate": 175},
    {"district": "Salyan", "location": "Salyankhalanga", "rate": 215},
    {"district": "Salyan", "location": "Shreenagar", "rate": 240},
    {"district": "Sankhuwasabha", "location": "Chainpur", "rate": 290},
    {"district": "Sankhuwasabha", "location": "Khandbari", "rate": 290},
    {"district": "Sankhuwasabha", "location": "Tumlingtar", "rate": 290},
    {"district": "Saptari", "location": "Bariyapatti", "rate": 200},
    {"district": "Saptari", "location": "Bodebarsain", "rate": 200},
    {"district": "Saptari", "location": "Hanumannagar", "rate": 190},
    {"district": "Saptari", "location": "Kadmaha", "rate": 190},
    {"district": "Saptari", "location": "Kalyanpur", "rate": 200},
    {"district": "Saptari", "location": "Kanchanpur", "rate": 190},
    {"district": "Saptari", "location": "Mahadeva", "rate": 190},
    {"district": "Saptari", "location": "Phattepur", "rate": 200},
    {"district": "Saptari", "location": "Rajbiraj", "rate": 180},
    {"district": "Sarlahi", "location": "Barathawa", "rate": 200},
    {"district": "Sarlahi", "location": "Gair", "rate": 190},
    {"district": "Sarlahi", "location": "Godaita", "rate": 190},
    {"district": "Sarlahi", "location": "Haripur", "rate": 190},
    {"district": "Sarlahi", "location": "Hariwan", "rate": 195},
    {"district": "Sarlahi", "location": "Lalbandi", "rate": 190},
    {"district": "Sarlahi", "location": "Malangwa", "rate": 190},
    {"district": "Sarlahi", "location": "Putalichowk", "rate": 190},
    {"district": "Sindhuli", "location": "Bhiman", "rate": 240},
    {"district": "Sindhuli", "location": "Dudhauli", "rate": 215},
    {"district": "Sindhuli", "location": "Khurkot", "rate": 240},
    {"district": "Sindhuli", "location": "Sindhuli", "rate": 180},
    {"district": "Sindhupalchok", "location": "Bahrabise", "rate": 240},
    {"district": "Sindhupalchok", "location": "Chautara", "rate": 240},
    {"district": "Sindhupalchok", "location": "Melamchi", "rate": 240},
    {"district": "Siraha", "location": "Bhagwanpur", "rate": 200},
    {"district": "Siraha", "location": "Bishnupur", "rate": 190},
    {"district": "Siraha", "location": "Dhangadhimai", "rate": 190},
    {"district": "Siraha", "location": "Ganeshpur", "rate": 190},
    {"district": "Siraha", "location": "Kalyanpur", "rate": 200},
    {"district": "Siraha", "location": "Lahan", "rate": 180},
    {"district": "Siraha", "location": "Mirchaiya", "rate": 190},
    {"district": "Siraha", "location": "Siraha", "rate": 190},
    {"district": "Siraha", "location": "Sukhipur", "rate": 190},
    {"district": "Solukhumbu", "location": "Salleri", "rate": 290},
    {"district": "Solukhumbu", "location": "Tingla", "rate": 290},
    {"district": "Sunsari", "location": "Bhantabari", "rate": 240},
    {"district": "Sunsari", "location": "Bhedetar", "rate": 190},
    {"district": "Sunsari", "location": "Dharan", "rate": 170},
    {"district": "Sunsari", "location": "Duhabi", "rate": 175},
    {"district": "Sunsari", "location": "Inaruwa", "rate": 175},
    {"district": "Sunsari", "location": "Itahari", "rate": 140},
    {"district": "Sunsari", "location": "Jhumka", "rate": 175},
    {"district": "Sunsari", "location": "Kalabanjar", "rate": 190},
    {"district": "Sunsari", "location": "Laukahi", "rate": 195},
    {"district": "Sunsari", "location": "NetaChowk", "rate": 200},
    {"district": "Surkhet", "location": "Chinchu", "rate": 200},
    {"district": "Surkhet", "location": "Mehelkuna", "rate": 265},
    {"district": "Surkhet", "location": "Surkhet", "rate": 190},
    {"district": "Syangja", "location": "Galyang", "rate": 215},
    {"district": "Syangja", "location": "Putalibazar", "rate": 190},
    {"district": "Syangja", "location": "Syangja", "rate": 190},
    {"district": "Syangja", "location": "Bayarghari", "rate": 200},
    {"district": "Syangja", "location": "Chapakot", "rate": 190},
    {"district": "Syangja", "location": "Waling", "rate": 190},
    {"district": "Tanahu", "location": "Abukhaireni", "rate": 190},
    {"district": "Tanahu", "location": "Bandipur", "rate": 215},
    {"district": "Tanahu", "location": "Bhimad", "rate": 210},
    {"district": "Tanahu", "location": "Damauli", "rate": 180},
    {"district": "Tanahu", "location": "Duipiple", "rate": 290},
    {"district": "Tanahu", "location": "Dulegauda", "rate": 200},
    {"district": "Tanahu", "location": "Dumre", "rate": 180},
    {"district": "Tanahu", "location": "Mugling", "rate": 200},
    {"district": "Taplejung", "location": "Taplejung", "rate": 275},
    {"district": "Terhathum", "location": "Basantapur", "rate": 290},
    {"district": "Terhathum", "location": "Jirikhimti", "rate": 290},
    {"district": "Terhathum", "location": "Myanglung", "rate": 290},
    {"district": "Udayapur", "location": "Beltar", "rate": 240},
    {"district": "Udayapur", "location": "Gaighat", "rate": 190},
    {"district": "Udayapur", "location": "Golbazar", "rate": 190},
    {"district": "Udayapur", "location": "Katari", "rate": 200},
    {"district": "Udayapur", "location": "Rampur", "rate": 240}
];

class ECommerceApp {
    constructor() {
        this.currentUser = null;
        this.cart = JSON.parse(localStorage.getItem('cart')) || [];
        this.products = [];
        this.flashSaleProducts = [];
        this.categories = [];
        this.isLoading = false;
        // Use relative path for single server setup
        this.apiBase = window.API_BASE_URL || '';
        this.api = new APIClient();
        this.googleAuth = new GoogleAuth();

        // Fast search state
        this.searchResults = [];
        this.isSearching = false;
        this.searchQuery = '';
        this.selectedSearchIndex = -1;
        this.searchDropdownVisible = false;

        // Debounced search handler for performance (150ms delay)
        this.debouncedSearch = debounce((query) => this.performSearch(query), 150);

        // Login status for discount
        this.isLoggedIn = false;
        this.discountPercent = 0;

        // Product click tracking for CTR-based recommendations
        this.productClicks = JSON.parse(localStorage.getItem('productClicks')) || {};

        this.init();
    }

    // Track product click
    trackProductClick(productId) {
        this.productClicks[productId] = (this.productClicks[productId] || 0) + 1;
        localStorage.setItem('productClicks', JSON.stringify(this.productClicks));
    }

    async init() {
        await this.loadInitialData();
        // Check login status for member discount
        await this.checkLoginStatus();
        // Initialize Google Auth
        try {
            await this.googleAuth.init();
            console.log('Google Auth initialized successfully');
            
            // Check if we're returning from Google OAuth redirect
            const authResult = this.googleAuth.handleRedirectCallback();
            if (authResult) {
                if (authResult.success) {
                    console.log('🎉 Google OAuth redirect successful!');
                    console.log('📤 Sending token to backend for authentication...');

                    // Send token to backend for authentication (same as popup flow)
                    try {
                        const response = await fetch(`${this.apiBase}/api/google-auth/`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            credentials: 'include',
                            body: JSON.stringify({
                                idToken: authResult.idToken,
                                accessToken: authResult.accessToken || authResult.idToken
                            })
                        });

                        const data = await response.json();
                        console.log('📥 Backend response:', data);

                        if (data.success) {
                            // Store user info with backend data
                            this.currentUser = {
                                ...data.user,
                                login_method: 'google',
                                picture: data.user.picture || authResult.user.picture
                            };
                            localStorage.setItem('currentUser', JSON.stringify(this.currentUser));

                            this.showNotification(data.message, 'success');

                            // Always go to home - user can click Admin Dashboard button if needed
                            setTimeout(() => {
                                this.navigate('/');
                            }, 1000);
                        } else {
                            console.error('❌ Backend auth failed:', data);
                            this.showNotification('Authentication failed: ' + data.error, 'error');
                        }
                    } catch (error) {
                        console.error('❌ Backend authentication error:', error);
                        this.showNotification('Failed to authenticate with server', 'error');
                    }
                } else {
                    console.error('❌ Google OAuth redirect failed:', authResult.error);
                    this.showNotification('Google sign-in failed: ' + authResult.error, 'error');
                }
            }
        } catch (error) {
            console.warn('Google Auth failed to initialize:', error);
        }
        this.setupEventListeners();
        this.checkAuthStatus();
        this.handleInitialRoute();
        this.renderApp();
    }

    async loadInitialData() {
        try {
            this.isLoading = true;
            // Try to load from API first, fallback to mock data
            // Fetch real data from backend API
            console.log('Fetching products from backend...');
            try {
                const [categoriesData, productsData, flashSaleData] = await Promise.all([
                    this.api.getCategories(),
                    this.api.getProducts(),
                    this.api.getFlashSaleProducts()
                ]);

                if (categoriesData && categoriesData.length > 0) {
                    this.categories = categoriesData;
                    console.log(`✅ Loaded ${categoriesData.length} categories from API`);
                } else {
                    console.log('⚠️ No categories from API, using mock data');
                    this.categories = await this.getMockCategories();
                }

                if (productsData && productsData.length > 0) {
                    this.products = productsData;
                    console.log(`✅ Loaded ${productsData.length} products from API`);
                } else {
                    console.log('⚠️ No products from API, using mock data');
                    this.products = await this.getMockProducts();
                }

                if (flashSaleData && flashSaleData.length > 0) {
                    this.flashSaleProducts = flashSaleData;
                    console.log(`✅ Loaded ${flashSaleData.length} flash sale products from API`);
                }
            } catch (error) {
                console.error('❌ Failed to fetch from API, using mock data:', error);
                this.categories = await this.getMockCategories();
                this.products = await this.getMockProducts();
            }
        } catch (error) {
            console.error('Failed to load initial data:', error);
            // Last resort fallback
            this.categories = await this.getMockCategories();
            this.products = await this.getMockProducts();
        } finally {
            this.isLoading = false;
            // Build search index after products are loaded
            if (this.products && this.products.length > 0) {
                searchEngine.buildIndex(this.products);
                console.log(`🔍 Search index built for ${this.products.length} products`);
            }
        }
    }

    // Mock data - will be replaced with API calls
    async getMockCategories() {
        return [
            { id: 1, name: 'Electronics', slug: 'electronics', image: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzY2N2VlYSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPkVsZWN0cm9uaWNzPC90ZXh0Pjwvc3ZnPg==' },
            { id: 2, name: 'Fashion', slug: 'fashion', image: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzc2NGJhMiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPkZhc2hpb248L3RleHQ+PC9zdmc+' },
            { id: 3, name: 'Home & Garden', slug: 'home-garden', image: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YwOTNmYiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPkhvbWUgJmFtcDsgR2FyZGVuPC90ZXh0Pjwvc3ZnPg==' },
            { id: 4, name: 'Sports', slug: 'sports', image: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzRmYWNmZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPlNwb3J0czwvdGV4dD48L3N2Zz4=' },
            { id: 5, name: 'Books', slug: 'books', image: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzQzZTk3YiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPkJvb2tzPC90ZXh0Pjwvc3ZnPg==' },
        ];
    }

    async getMockProducts() {
        return [
            {
                id: 1, name: 'Wireless Headphones Pro', category: 'Electronics',
                price: 299.99, compare_price: 399.99, image: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzY2N2VlYSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPkhlYWRwaG9uZXM8L3RleHQ+PC9zdmc+',
                rating: 4.8, reviews: 1247, stock_status: 'in_stock'
            },
            {
                id: 2, name: 'Smart Fitness Watch', category: 'Electronics',
                price: 199.99, compare_price: 249.99, image: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzRmYWNmZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPlNtYXJ0IFdhdGNoPC90ZXh0Pjwvc3ZnPg==',
                rating: 4.6, reviews: 856, stock_status: 'in_stock'
            },
            {
                id: 3, name: 'Designer Jacket', category: 'Fashion',
                price: 159.99, compare_price: null, image: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzc2NGJhMiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPkphY2tldDwvdGV4dD48L3N2Zz4=',
                rating: 4.7, reviews: 423, stock_status: 'low_stock'
            },
            {
                id: 4, name: 'Coffee Maker Deluxe', category: 'Home & Garden',
                price: 89.99, compare_price: 129.99, image: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iIzQzZTk3YiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPkNvZmZlZSBNYWtlcjwvdGV4dD48L3N2Zz4=',
                rating: 4.5, reviews: 672, stock_status: 'in_stock'
            }
        ];
    }

    checkAuthStatus() {
        // Check if user is logged in by checking session/localStorage
        const userData = localStorage.getItem('currentUser');
        if (userData) {
            this.currentUser = JSON.parse(userData);
        }

        // Verify with server that session is still valid
        fetch('/api/auth-status/', {
            credentials: 'include'
        })
            .then(res => res.json())
            .then(data => {
                if (data.authenticated) {
                    // Server confirms logged in - update user data
                    this.currentUser = data.user;
                    localStorage.setItem('currentUser', JSON.stringify(data.user));
                } else {
                    // Server says not logged in - clear local state
                    this.currentUser = null;
                    localStorage.removeItem('currentUser');
                }
                // Re-render to update UI
                this.renderApp();
            })
            .catch(err => {
                console.error('Error checking auth status:', err);
            });
    }

    setupEventListeners() {
        // Navigation events
        document.addEventListener('click', (e) => {
            // Handle data-route navigation
            if (e.target.matches('[data-route]') || e.target.closest('[data-route]')) {
                e.preventDefault();
                const target = e.target.matches('[data-route]') ? e.target : e.target.closest('[data-route]');
                console.log('Navigating to:', target.dataset.route);
                this.navigate(target.dataset.route);
            }
            
            if (e.target.matches('.add-to-cart')) {
                e.preventDefault();
                this.addToCart(e.target.dataset.productId);
            }
            
            if (e.target.matches('.cart-toggle') || e.target.closest('.cart-toggle')) {
                e.preventDefault();
                this.toggleCart();
            }

            if (e.target.matches('.admin-dashboard-btn')) {
                e.preventDefault();
                // First verify session with backend, then navigate
                this.goToAdminDashboard();
            }
            
            if (e.target.matches('.visit-store-btn')) {
                e.preventDefault();
                this.navigate('/');
            }

            if (e.target.matches('.google-login-btn') || e.target.matches('.google-login-btn-modern')) {
                e.preventDefault();
                this.handleGoogleLogin();
            }

            if (e.target.matches('.logout-btn')) {
                e.preventDefault();
                this.handleLogout();
            }

            // Search button click
            if (e.target.matches('.search-btn') || e.target.closest('.search-btn')) {
                e.preventDefault();
                const searchInput = document.querySelector('.search-input');
                if (searchInput && searchInput.value.trim()) {
                    this.hideSearchDropdown();
                    this.navigate(`/products?search=${encodeURIComponent(searchInput.value.trim())}`);
                }
            }
        });

        // Search functionality with keyboard navigation
        document.addEventListener('input', (e) => {
            if (e.target.matches('.search-input')) {
                this.handleSearch(e.target.value);
            }
        });

        // Search keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (!e.target.matches('.search-input')) return;

            const dropdown = document.querySelector('.search-dropdown');
            if (!dropdown || !this.searchDropdownVisible) {
                // If Enter pressed without dropdown, perform search and go to products page
                if (e.key === 'Enter' && this.searchQuery.trim()) {
                    e.preventDefault();
                    this.navigate(`/products?search=${encodeURIComponent(this.searchQuery)}`);
                    this.hideSearchDropdown();
                }
                return;
            }

            const items = dropdown.querySelectorAll('.search-result-item');
            const maxIndex = items.length - 1;

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.selectedSearchIndex = Math.min(this.selectedSearchIndex + 1, maxIndex);
                    this.updateSearchSelection(items);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.selectedSearchIndex = Math.max(this.selectedSearchIndex - 1, -1);
                    this.updateSearchSelection(items);
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (this.selectedSearchIndex >= 0 && items[this.selectedSearchIndex]) {
                        items[this.selectedSearchIndex].click();
                    } else if (this.searchQuery.trim()) {
                        this.navigate(`/products?search=${encodeURIComponent(this.searchQuery)}`);
                        this.hideSearchDropdown();
                    }
                    break;
                case 'Escape':
                    this.hideSearchDropdown();
                    e.target.blur();
                    break;
            }
        });

        // Close search dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideSearchDropdown();
            }
        });

        // Focus search input on "/" key
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                e.preventDefault();
                const searchInput = document.querySelector('.search-input');
                if (searchInput) searchInput.focus();
            }
        });

        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.login-form') || e.target.matches('.modern-login-form')) {
                e.preventDefault();
                this.handleLogin(e.target);
            }
            
            if (e.target.matches('.newsletter-form')) {
                e.preventDefault();
                this.handleNewsletterSignup(e.target);
            }
        });
    }

    navigate(route) {
        window.scrollTo(0, 0);
        history.pushState({}, '', route);

        // Track product clicks for CTR
        const productMatch = route.match(/^\/product\/(\d+)$/);
        if (productMatch) {
            this.trackProductClick(productMatch[1]);
        }

        this.renderApp();
    }

    // Handle initial route on page load
    handleInitialRoute() {
        const currentPath = window.location.pathname;
        const hash = window.location.hash;
        
        // Handle hash routing as fallback
        if (hash && hash.startsWith('#/')) {
            const route = hash.substring(1);
            history.replaceState({}, '', route);
        }
        
        // Handle direct navigation to any route
        this.renderApp();
    }

    renderApp() {
        const currentPath = window.location.pathname;
        const app = document.getElementById('app');
        
        if (!app) return;

        let content = '';
        
        console.log('Current path:', currentPath); // Debug log

        // Check for product detail page
        const productMatch = currentPath.match(/^\/product\/(\d+)$/);
        const checkoutMatch = currentPath === '/checkout';
        const orderConfirmMatch = currentPath.match(/^\/order-confirmation\/(.+)$/);
        const orderDetailMatch = currentPath.match(/^\/my-orders\/([a-f0-9-]+)$/i);

        switch (true) {
            case currentPath === '/products':
                content = this.renderProductsPage();
                break;
            case currentPath === '/categories':
                content = this.renderCategoriesPage();
                break;
            case currentPath === '/about':
                content = this.renderAboutPage();
                break;
            case currentPath === '/contact':
                content = this.renderContactPage();
                break;
            case currentPath === '/login':
                content = this.renderLoginPage();
                break;
            case currentPath === '/register':
                content = this.renderRegisterPage();
                break;
            case currentPath === '/cart':
                content = this.renderCartPage();
                break;
            case currentPath === '/my-orders':
                content = this.renderOrdersPage();
                break;
            case !!orderDetailMatch:
                content = this.renderOrderDetailPage(orderDetailMatch[1]);
                break;
            case !!productMatch:
                content = this.renderProductDetailPage(productMatch[1]);
                break;
            case checkoutMatch:
                content = this.renderCheckoutPage();
                break;
            case !!orderConfirmMatch:
                content = this.renderOrderConfirmationPage(orderConfirmMatch[1]);
                break;
            default:
                // For login/register pages, don't show header/footer
                if (currentPath === '/login' || currentPath === '/register') {
                    app.innerHTML = currentPath === '/login' ? this.renderLoginPage() : this.renderRegisterPage();
                    this.initializeInteractiveComponents();
                    return;
                }
                content = this.renderHomePage();
        }

        app.innerHTML = `
            ${this.renderHeader()}
            <main class="main-content">
                ${content}
            </main>
            ${this.renderFloatingCart()}
            ${this.renderFooter()}
        `;

        // Initialize interactive components after render
        this.initializeInteractiveComponents();
        
        // Handle browser back/forward buttons (only add once)
        if (!this.popStateListenerAdded) {
            window.addEventListener('popstate', () => {
                this.renderApp();
            });
            this.popStateListenerAdded = true;
        }
    }

    renderHeader() {
        const cartItemCount = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        
        return `
            <header class="header">
                <div class="header-container">
                    <div class="header-left">
                        <div class="logo">
                            <a href="/" data-route="/" style="text-decoration: none; color: inherit; display: flex; align-items: center; gap: 12px;">
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 22px; color: white; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
                                    O
                                </div>
                                <span class="logo-text" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800; font-size: 24px;">OVN Store</span>
                            </a>
                        </div>
                    </div>
                    
                    <div class="header-center">
                        <div class="search-container">
                            <input type="text" class="search-input" placeholder="Search products, brands, categories...">
                            <button class="search-btn">
                                <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M21.71 20.29L18 16.61A9 9 0 1 0 16.61 18l3.68 3.68a1 1 0 0 0 1.42-1.42zM11 18a7 7 0 1 1 7-7 7 7 0 0 1-7 7z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    
                    <div class="header-right">
                        <nav class="nav-links">
                            <a href="/products" data-route="/products">Products</a>
                            <a href="/categories" data-route="/categories">Categories</a>
                            <a href="/about" data-route="/about">About</a>
                            <a href="/contact" data-route="/contact">Contact</a>
                        </nav>
                        
                        <div class="user-actions">
                            <button class="cart-toggle">
                                <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M7 18c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.15.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12L8.1 13h7.45c.75 0 1.41-.41 1.75-1.03L21.7 4H5.21l-.94-2H1zm16 16c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                                </svg>
                                <span class="cart-count">${cartItemCount}</span>
                            </button>

                            ${this.currentUser ? `
                                <div class="user-menu">
                                    <div class="user-info">
                                        ${this.currentUser.picture ?
                                            `<img src="${this.currentUser.picture}" alt="Profile" class="user-avatar-img">` :
                                            `<span class="user-avatar-icon">
                                                <svg width="20" height="20" fill="#374151" viewBox="0 0 24 24">
                                                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                                                </svg>
                                            </span>`
                                        }
                                        <span class="user-name">${this.currentUser.first_name || this.currentUser.username?.split(/[^a-zA-Z]/)[0] || 'User'}</span>
                                    </div>
                                    <div class="user-actions-menu">
                                        <a href="/my-orders" data-route="/my-orders" style="display: flex; align-items: center; gap: 8px; padding: 12px 20px; color: #374151; text-decoration: none; border-radius: 8px; margin-bottom: 8px; background: #f3f4f6; font-weight: 500;">
                                            <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l4.59-4.58L18 11l-6 6z"/>
                                            </svg>
                                            My Orders
                                        </a>
                                        ${this.currentUser.is_staff || this.currentUser.is_superuser ? `
                                            <button class="admin-dashboard-btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: 600; margin-bottom: 8px; cursor: pointer; width: 100%; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; gap: 8px;">
                                                <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                                    <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
                                                </svg>
                                                Admin Dashboard
                                            </button>
                                        ` : ''}
                                        <button class="logout-btn">
                                            <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M16 13v-2H7V8l-5 4 5 4v-3h9z"/>
                                                <path d="M20 3h-9c-1.103 0-2 .897-2 2v4h2V5h9v14h-9v-4H9v4c0 1.103.897 2 2 2h9c1.103 0 2-.897 2-2V5c0-1.103-.897-2-2-2z"/>
                                            </svg>
                                            Logout
                                        </button>
                                    </div>
                                </div>
                            ` : `
                                <a href="/login" data-route="/login" class="login-btn">Login</a>
                                <a href="/register" data-route="/register" class="register-btn">Register</a>
                            `}
                        </div>
                    </div>
                </div>
            </header>
        `;
    }

    renderHomePage() {
        return `
            <div class="home-page">
                ${this.renderHeroSection()}
                ${this.renderFlashSaleSection()}
                ${this.renderFeaturedProducts()}
            </div>
        `;
    }

    renderFlashSaleSection() {
        if (!this.flashSaleProducts || this.flashSaleProducts.length === 0) {
            return '';
        }

        const formatPrice = (num) => num.toLocaleString('en-IN');

        return `
            <section class="flash-sale-section">
                <div class="container">
                    <div class="flash-sale-header">
                        <div class="flash-sale-title">
                            <i class="fas fa-bolt"></i>
                            <h2>Flash Sale</h2>
                            <span class="flash-badge">Limited Time</span>
                        </div>
                    </div>
                    <div class="flash-sale-scroll">
                        ${this.flashSaleProducts.map(product => {
                            const price = product.price;
                            const comparePrice = product.compare_price;
                            let discount = 0;
                            let sellingPrice = price;
                            let originalPrice = comparePrice;

                            if (comparePrice && comparePrice !== price) {
                                if (comparePrice < price) {
                                    sellingPrice = comparePrice;
                                    originalPrice = price;
                                    discount = Math.round(((price - comparePrice) / price) * 100);
                                } else {
                                    sellingPrice = price;
                                    originalPrice = comparePrice;
                                    discount = Math.round(((comparePrice - price) / comparePrice) * 100);
                                }
                            }

                            return `
                                <div class="flash-sale-card" onclick="window.app.navigate('/product/${product.id}')">
                                    <div class="flash-sale-image">
                                        <img src="${product.image}" alt="${product.name}">
                                        ${discount > 0 ? `<div class="flash-discount-badge">-${discount}%</div>` : ''}
                                    </div>
                                    <div class="flash-sale-info">
                                        <h4 class="flash-product-name">${product.name}</h4>
                                        <div class="flash-product-price">
                                            <span class="flash-current-price">Rs. ${formatPrice(sellingPrice)}</span>
                                            ${originalPrice ? `<span class="flash-original-price">Rs. ${formatPrice(originalPrice)}</span>` : ''}
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </section>
        `;
    }

    renderHeroSection() {
        // Get first 3 products for initial display
        const floatingProducts = this.products.slice(0, 3);
        const badges = ['HOT', 'NEW', 'SALE'];

        // Start the floating product carousel after render
        setTimeout(() => this.startFloatingProductCarousel(), 500);

        return `
            <section class="hero-section hero-banner-style">
                <div class="hero-gradient-bg">
                    <div class="floating-shape shape-1"></div>
                    <div class="floating-shape shape-2"></div>
                    <div class="floating-shape shape-3"></div>
                </div>
                <div class="hero-main-content">
                    <div class="hero-text-side">
                        <h1 class="hero-banner-title">
                            <span class="glow-text">Discover</span>
                            <span class="glow-text gradient-glow">Tomorrow's</span>
                            <span class="glow-text">Shopping</span>
                        </h1>
                        <p class="hero-banner-subtitle">
                            Experience the future of e-commerce with our revolutionary platform.
                            Cutting-edge technology meets unparalleled user experience.
                        </p>
                        <div class="hero-stats">
                            <div class="hero-stat">
                                <span class="stat-num">50K+</span>
                                <span class="stat-label">Happy Customers</span>
                            </div>
                            <div class="hero-stat">
                                <span class="stat-num">4.9</span>
                                <span class="stat-label">Rating</span>
                            </div>
                            <div class="hero-stat">
                                <span class="stat-num">500+</span>
                                <span class="stat-label">Products</span>
                            </div>
                        </div>
                        <a href="/products" data-route="/products" class="hero-banner-btn">
                            Explore Products
                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/>
                            </svg>
                        </a>
                    </div>
                    <div class="hero-floating-side">
                        <!-- Floating Product Cards -->
                        ${floatingProducts.map((product, index) => {
                            const displayPrice = product.compare_price || product.price;
                            return `
                            <div class="floating-product float-${index + 1}" data-slot="${index}" data-product-id="${product.id}">
                                <div class="fp-badge">${badges[index]}</div>
                                <div class="fp-image-wrap">
                                    <img src="${product.image}" alt="${product.name}" loading="lazy">
                                </div>
                                <div class="floating-product-info">
                                    <div class="fp-stars">${this.renderStars(product.rating)}</div>
                                    <span class="fp-name">${product.name.substring(0, 14)}${product.name.length > 14 ? '...' : ''}</span>
                                    <span class="fp-price">Rs. ${displayPrice.toLocaleString()}</span>
                                </div>
                                <div class="fp-glow"></div>
                            </div>
                        `}).join('')}
                    </div>
                </div>
            </section>
        `;
    }

    // Helper function to render stars
    renderStars(rating) {
        const stars = [];
        const fullStars = Math.floor(rating || 4.5);
        for (let i = 0; i < 5; i++) {
            stars.push(`<i class="fas fa-star" style="opacity: ${i < fullStars ? 1 : 0.3}"></i>`);
        }
        return stars.join('');
    }

    // Floating product carousel - simple smooth transition
    startFloatingProductCarousel() {
        if (this.floatingCarouselInterval) {
            clearInterval(this.floatingCarouselInterval);
        }

        const badges = ['HOT', 'NEW', 'SALE'];
        let currentSlot = 0;
        let productIndices = [0, 1, 2];
        const totalProducts = this.products.length;

        if (totalProducts <= 3) return;

        this.floatingCarouselInterval = setInterval(() => {
            const floatingCards = document.querySelectorAll('.floating-product');
            if (floatingCards.length === 0) {
                clearInterval(this.floatingCarouselInterval);
                return;
            }

            const card = floatingCards[currentSlot];
            if (!card) return;

            // Calculate next product index
            let nextProductIndex = productIndices[currentSlot] + 3;
            if (nextProductIndex >= totalProducts) {
                nextProductIndex = currentSlot;
            }
            productIndices[currentSlot] = nextProductIndex;

            const product = this.products[nextProductIndex];
            if (!product) return;

            const displayPrice = product.compare_price || product.price;
            const img = card.querySelector('.fp-image-wrap img');

            // Preload new image
            const newImg = new Image();
            newImg.src = product.image;

            newImg.onload = () => {
                // Smooth transition on image
                img.style.transition = 'opacity 0.8s ease-in-out';
                img.style.opacity = '0.3';

                setTimeout(() => {
                    // Update all content
                    card.dataset.productId = product.id;
                    card.querySelector('.fp-badge').textContent = badges[currentSlot];
                    img.src = product.image;
                    img.alt = product.name;
                    card.querySelector('.fp-stars').innerHTML = this.renderStars(product.rating);
                    card.querySelector('.fp-name').textContent = product.name.substring(0, 14) + (product.name.length > 14 ? '...' : '');
                    card.querySelector('.fp-price').textContent = `Rs. ${displayPrice.toLocaleString()}`;
                    card.onclick = () => window.app.navigate(`/product/${product.id}`);

                    // Fade back in
                    img.style.opacity = '1';
                }, 400);
            };

            currentSlot = (currentSlot + 1) % 3;

        }, 3000);
    }

    renderFeaturedCategories() {
        return `
            <section class="featured-categories">
                <div class="container">
                    <div class="section-header">
                        <h2 class="section-title">Shop by Category</h2>
                        <p class="section-subtitle">Discover our carefully curated collections</p>
                    </div>
                    <div class="categories-grid">
                        ${this.categories.map(category => `
                            <div class="category-card" data-category="${category.slug}">
                                <div class="category-image">
                                    <img src="${category.image}" alt="${category.name}">
                                    <div class="category-overlay">
                                        <button class="category-cta">Shop Now</button>
                                    </div>
                                </div>
                                <div class="category-info">
                                    <h3 class="category-name">${category.name}</h3>
                                    <p class="category-count">${Math.floor(Math.random() * 100) + 20}+ Products</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </section>
        `;
    }

    renderFeaturedProducts() {
        const featuredProducts = this.products;
        
        return `
            <section class="featured-products">
                <div class="container">
                    <div class="section-header">
                        <h2 class="section-title">Just for you</h2>
                    </div>
                    <div class="products-grid">
                        ${featuredProducts.map(product => this.renderProductCard(product)).join('')}
                    </div>
                </div>
            </section>
        `;
    }

    renderProductCard(product) {
        // Calculate discount - works regardless of which field has higher value
        let discount = 0;
        if (product.compare_price && product.compare_price !== product.price) {
            const higher = Math.max(product.price, product.compare_price);
            const lower = Math.min(product.price, product.compare_price);
            discount = Math.round(((higher - lower) / higher) * 100);
        }

        return `
            <div class="product-card" data-product-id="${product.id}">
                <a href="/product/${product.id}" data-route="/product/${product.id}" class="product-image-link">
                    <div class="product-image-container">
                        <img src="${product.image}" alt="${product.name}" class="product-image">
                        ${discount > 0 ? `<div class="product-badge">${discount}% OFF</div>` : ''}
                        <div class="product-overlay">
                            <span class="view-product">View Product</span>
                        </div>
                    </div>
                </a>
                <div class="product-actions-floating">
                    <button class="action-btn quick-view" title="Quick View" onclick="event.stopPropagation(); window.app.navigate('/product/${product.id}')">
                        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                        </svg>
                    </button>
                </div>
                <div class="product-info">
                    <a href="/product/${product.id}" data-route="/product/${product.id}" class="product-name-link">
                        <h3 class="product-name">${product.name}</h3>
                    </a>
                    <div class="product-rating">
                        <div class="stars">
                            ${Array(5).fill().map((_, i) => `
                                <span class="star ${i < Math.floor(product.rating) ? 'filled' : ''}">⭐</span>
                            `).join('')}
                        </div>
                        <span class="rating-text">(${product.reviews})</span>
                    </div>
                    <div class="product-pricing">
                        ${(() => {
                            const price = product.price;
                            const comparePrice = product.compare_price;

                            // Format number with commas
                            const formatPrice = (num) => num.toLocaleString('en-IN');

                            // Determine which is selling price and which is MRP
                            if (comparePrice && comparePrice < price) {
                                const discountPercent = Math.round(((price - comparePrice) / price) * 100);
                                return `
                                    <span class="current-price">Rs. ${formatPrice(comparePrice)}</span>
                                    <span class="original-price-wrap">
                                        <span class="original-price">Rs. ${formatPrice(price)}</span><sup class="discount-percent">-${discountPercent}%</sup>
                                    </span>
                                `;
                            } else if (comparePrice && comparePrice > price) {
                                const discountPercent = Math.round(((comparePrice - price) / comparePrice) * 100);
                                return `
                                    <span class="current-price">Rs. ${formatPrice(price)}</span>
                                    <span class="original-price-wrap">
                                        <span class="original-price">Rs. ${formatPrice(comparePrice)}</span><sup class="discount-percent">-${discountPercent}%</sup>
                                    </span>
                                `;
                            } else {
                                return `<span class="current-price">Rs. ${formatPrice(price)}</span>`;
                            }
                        })()}
                    </div>
                    <div class="product-buttons">
                        <button type="button" class="add-to-cart-btn ${product.stock_status === 'out_of_stock' ? 'disabled' : ''}"
                                onclick="event.preventDefault(); event.stopPropagation(); window.app.addToCart(${product.id}); return false;"
                                ${product.stock_status === 'out_of_stock' ? 'disabled' : ''}>
                            <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M11 9h2V6h3V4h-3V1h-2v3H8v2h3v3zm-4 9c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zm10 0c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2zm-9.83-3.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.86-7.01L19.42 4h-.01l-1.1 2-2.76 5H8.53l-.13-.27L6.16 6l-.95-2-.94-2H1v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25z"/>
                            </svg>
                            ${product.stock_status === 'out_of_stock' ? 'Out of Stock' : 'Cart'}
                        </button>
                        <button type="button" class="buy-now-btn ${product.stock_status === 'out_of_stock' ? 'disabled' : ''}"
                                onclick="event.preventDefault(); event.stopPropagation(); window.app.buyNow(${product.id}); return false;"
                                ${product.stock_status === 'out_of_stock' ? 'disabled' : ''}>
                            <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
                            </svg>
                            Buy
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderRelatedProductCard(product) {
        const price = product.price;
        const comparePrice = product.compare_price;
        const formatPrice = (num) => num.toLocaleString('en-IN');

        let priceHtml = '';
        if (comparePrice && comparePrice < price) {
            const discountPercent = Math.round(((price - comparePrice) / price) * 100);
            priceHtml = `
                <span class="related-current-price">Rs. ${formatPrice(comparePrice)}</span>
                <span class="related-original-price">Rs. ${formatPrice(price)}</span>
                <span class="related-discount">-${discountPercent}%</span>
            `;
        } else if (comparePrice && comparePrice > price) {
            const discountPercent = Math.round(((comparePrice - price) / comparePrice) * 100);
            priceHtml = `
                <span class="related-current-price">Rs. ${formatPrice(price)}</span>
                <span class="related-original-price">Rs. ${formatPrice(comparePrice)}</span>
                <span class="related-discount">-${discountPercent}%</span>
            `;
        } else {
            priceHtml = `<span class="related-current-price">Rs. ${formatPrice(price)}</span>`;
        }

        return `
            <div class="related-product-card" onclick="window.app.navigate('/product/${product.id}')">
                <div class="related-product-image">
                    <img src="${product.image}" alt="${product.name}">
                </div>
                <div class="related-product-info">
                    <h4 class="related-product-name">${product.name}</h4>
                    <div class="related-product-rating">
                        <span class="stars">⭐ ${product.rating}</span>
                        <span class="reviews">(${product.reviews})</span>
                    </div>
                    <div class="related-product-price">
                        ${priceHtml}
                    </div>
                </div>
            </div>
        `;
    }

    renderNewsletterSection() {
        return `
            <section class="newsletter-section">
                <div class="container">
                    <div class="newsletter-content">
                        <div class="newsletter-text">
                            <h2>Stay in the Loop</h2>
                            <p>Get exclusive deals, new product announcements, and insider tips delivered to your inbox.</p>
                        </div>
                        <div class="newsletter-form">
                            <input type="email" placeholder="Enter your email address">
                            <button type="submit">Subscribe</button>
                        </div>
                    </div>
                </div>
            </section>
        `;
    }

    renderFooter() {
        return `
            <footer style="background: none; padding: 20px 0; text-align: center;">
                <p style="color: #000; margin: 0; font-size: 0.9rem;">&copy; 2024 OVN Store. All rights reserved.</p>
            </footer>
        `;
    }

    renderFloatingCart() {
        // Removed floating cart as per user request
        return '';
    }

    renderLoginPage() {
        return `
            <div class="ultra-modern-auth-page">
                <!-- Minimal Background -->
                <div class="auth-bg-minimal">
                    <div class="bg-gradient-1"></div>
                    <div class="bg-gradient-2"></div>
                </div>
                
                <!-- Main Container -->
                <div class="auth-container-clean">
                    <!-- Header -->
                    <div class="auth-header-clean">
                        <div class="brand-logo-clean">
                            <span class="logo-icon-clean">🛍️</span>
                            <span class="logo-text-clean">OVN Store</span>
                        </div>
                        <div class="auth-title-section">
                            <h1 class="auth-title-clean">Welcome back</h1>
                            <p class="auth-subtitle-clean">Sign in to continue your shopping journey</p>
                        </div>
                    </div>
                    
                    <!-- Form Section -->
                    <div class="auth-form-clean">
                        <!-- Google Sign-in -->
                        <button type="button" class="google-btn-clean google-login-btn-modern">
                            <svg width="20" height="20" viewBox="0 0 24 24" class="google-icon-clean">
                                <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                            </svg>
                            Continue with Google
                        </button>
                        
                        <!-- Divider -->
                        <div class="divider-clean">
                            <span class="divider-text-clean">or</span>
                        </div>
                        
                        <!-- Email Form -->
                        <form class="login-form-clean modern-login-form" novalidate>
                            <div class="input-group-clean">
                                <input type="email" id="email-clean" name="username" class="input-clean" placeholder=" " required>
                                <label for="email-clean" class="label-clean">Email address</label>
                                <div class="input-border-clean"></div>
                            </div>
                            
                            <div class="input-group-clean">
                                <input type="password" id="password-clean" name="password" class="input-clean" placeholder=" " required>
                                <label for="password-clean" class="label-clean">Password</label>
                                <div class="input-border-clean"></div>
                                <button type="button" class="password-toggle-clean">
                                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                                    </svg>
                                </button>
                            </div>
                            
                            <div class="form-options-clean">
                                <label class="checkbox-clean">
                                    <input type="checkbox" name="remember">
                                    <span class="checkbox-mark"></span>
                                    <span class="checkbox-text">Remember me</span>
                                </label>
                                <a href="#" class="forgot-link-clean">Forgot password?</a>
                            </div>
                            
                            <button type="submit" class="submit-btn-clean">
                                <span class="btn-text-clean">Sign In</span>
                                <div class="btn-loader-clean">
                                    <div class="loader-spinner"></div>
                                </div>
                            </button>
                        </form>
                        
                        <!-- Footer -->
                        <div class="auth-footer-clean">
                            <p class="footer-text-clean">
                                Don't have an account? 
                                <a href="/register" data-route="/register" class="signup-link-clean">Sign up</a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderRegisterPage() {
        return `
            <div class="ultra-modern-auth-page">
                <!-- Minimal Background -->
                <div class="auth-bg-minimal">
                    <div class="bg-gradient-1"></div>
                    <div class="bg-gradient-2"></div>
                </div>
                
                <!-- Main Container -->
                <div class="auth-container-clean">
                    <!-- Header -->
                    <div class="auth-header-clean">
                        <div class="brand-logo-clean">
                            <span class="logo-icon-clean">🛍️</span>
                            <span class="logo-text-clean">OVN Store</span>
                        </div>
                        <div class="auth-title-section">
                            <h1 class="auth-title-clean">Create your account</h1>
                            <p class="auth-subtitle-clean">Join thousands of happy shoppers today</p>
                        </div>
                    </div>
                    
                    <!-- Form Section -->
                    <div class="auth-form-clean">
                        <!-- Google Sign-in -->
                        <button type="button" class="google-btn-clean google-login-btn-modern">
                            <svg width="20" height="20" viewBox="0 0 24 24" class="google-icon-clean">
                                <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                            </svg>
                            Continue with Google
                        </button>
                        
                        <!-- Divider -->
                        <div class="divider-clean">
                            <span class="divider-text-clean">or</span>
                        </div>
                        
                        <!-- Registration Form -->
                        <form class="register-form-clean modern-login-form" novalidate>
                            <div class="name-row-clean">
                                <div class="input-group-clean">
                                    <input type="text" id="firstName-clean" name="firstName" class="input-clean" placeholder=" " required>
                                    <label for="firstName-clean" class="label-clean">First name</label>
                                    <div class="input-border-clean"></div>
                                </div>
                                <div class="input-group-clean">
                                    <input type="text" id="lastName-clean" name="lastName" class="input-clean" placeholder=" " required>
                                    <label for="lastName-clean" class="label-clean">Last name</label>
                                    <div class="input-border-clean"></div>
                                </div>
                            </div>
                            
                            <div class="input-group-clean">
                                <input type="email" id="email-register-clean" name="email" class="input-clean" placeholder=" " required>
                                <label for="email-register-clean" class="label-clean">Email address</label>
                                <div class="input-border-clean"></div>
                            </div>
                            
                            <div class="input-group-clean">
                                <input type="password" id="password-register-clean" name="password" class="input-clean" placeholder=" " required>
                                <label for="password-register-clean" class="label-clean">Password</label>
                                <div class="input-border-clean"></div>
                                <button type="button" class="password-toggle-clean">
                                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                                    </svg>
                                </button>
                            </div>
                            
                            <div class="input-group-clean">
                                <input type="password" id="confirmPassword-clean" name="confirmPassword" class="input-clean" placeholder=" " required>
                                <label for="confirmPassword-clean" class="label-clean">Confirm password</label>
                                <div class="input-border-clean"></div>
                                <button type="button" class="password-toggle-clean">
                                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                                    </svg>
                                </button>
                            </div>
                            
                            <div class="terms-agreement-clean">
                                <label class="checkbox-clean">
                                    <input type="checkbox" name="terms" required>
                                    <span class="checkbox-mark"></span>
                                    <span class="checkbox-text">I agree to the <a href="#" class="terms-link-clean">Terms of Service</a> and <a href="#" class="terms-link-clean">Privacy Policy</a></span>
                                </label>
                            </div>
                            
                            <button type="submit" class="submit-btn-clean">
                                <span class="btn-text-clean">Create Account</span>
                                <div class="btn-loader-clean">
                                    <div class="loader-spinner"></div>
                                </div>
                            </button>
                        </form>
                        
                        <!-- Footer -->
                        <div class="auth-footer-clean">
                            <p class="footer-text-clean">
                                Already have an account? 
                                <a href="/login" data-route="/login" class="signup-link-clean">Sign in</a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderProductsPage() {
        // Check for search query in URL
        const urlParams = new URLSearchParams(window.location.search);
        const searchQuery = urlParams.get('search') || '';

        // Filter products based on search query
        let displayProducts = this.products;
        let pageTitle = 'All Products';
        let pageSubtitle = 'Discover our amazing collection';

        if (searchQuery.trim()) {
            // Use the fast search engine
            displayProducts = searchEngine.search(searchQuery, 100);
            pageTitle = `Search Results for "${this.escapeHtml(searchQuery)}"`;
            pageSubtitle = `${displayProducts.length} product${displayProducts.length !== 1 ? 's' : ''} found`;
        }

        const noResultsHtml = searchQuery && displayProducts.length === 0 ? `
            <div class="search-no-results-page">
                <svg width="80" height="80" fill="#9ca3af" viewBox="0 0 24 24">
                    <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
                <h3>No products found</h3>
                <p>We couldn't find any products matching "${this.escapeHtml(searchQuery)}"</p>
                <p>Try a different search term or browse our categories</p>
                <a href="/products" data-route="/products" class="cta-primary">View All Products</a>
            </div>
        ` : '';

        return `
            <div class="products-page">
                <div class="container">
                    <div class="section-header">
                        <h2 class="section-title">${pageTitle}</h2>
                        <p class="section-subtitle">${pageSubtitle}</p>
                        ${searchQuery ? `
                            <a href="/products" data-route="/products" class="clear-search-btn">
                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                                </svg>
                                Clear Search
                            </a>
                        ` : ''}
                    </div>
                    ${noResultsHtml || `
                        <div class="products-grid">
                            ${displayProducts.map(product => this.renderProductCard(product)).join('')}
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    renderCategoriesPage() {
        return `
            <div class="categories-page">
                <div class="container">
                    <div class="section-header">
                        <h2 class="section-title">All Categories</h2>
                        <p class="section-subtitle">Browse our product categories</p>
                    </div>
                    <div class="categories-grid">
                        ${this.categories.map(category => `
                            <a href="/products?search=${encodeURIComponent(category.name)}" data-route="/products?search=${encodeURIComponent(category.name)}" class="category-card-link">
                                <div class="category-card-full">
                                    <div class="category-card-image">
                                        ${category.image ?
                                            `<img src="${category.image}" alt="${this.escapeHtml(category.name)}">` :
                                            `<div class="category-placeholder">
                                                <svg width="48" height="48" fill="#9ca3af" viewBox="0 0 24 24">
                                                    <path d="M4 8h4V4H4v4zm6 12h4v-4h-4v4zm-6 0h4v-4H4v4zm0-6h4v-4H4v4zm6 0h4v-4h-4v4zm6-10v4h4V4h-4zm-6 4h4V4h-4v4zm6 6h4v-4h-4v4zm0 6h4v-4h-4v4z"/>
                                                </svg>
                                            </div>`
                                        }
                                    </div>
                                    <div class="category-card-content">
                                        <h3 class="category-card-name">${this.escapeHtml(category.name)}</h3>
                                        <p class="category-card-count">${this.products.filter(p => p.category === category.name).length} products</p>
                                    </div>
                                </div>
                            </a>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    renderAboutPage() {
        return `
            <div class="about-page">
                <div class="about-hero">
                    <div class="about-hero-content">
                        <h1 class="about-title">About OVN Store</h1>
                        <p class="about-tagline">Your Trusted Shopping Destination in Nepal</p>
                    </div>
                    <div class="about-hero-bg"></div>
                </div>

                <div class="container">
                    <div class="about-content">
                        <section class="about-section">
                            <div class="about-section-icon">
                                <svg width="48" height="48" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                </svg>
                            </div>
                            <h2>Our Story</h2>
                            <p>OVN Store was founded with a simple mission: to bring quality products to customers across Nepal with exceptional service and competitive prices. What started as a small venture has grown into a trusted e-commerce platform serving thousands of happy customers nationwide.</p>
                        </section>

                        <section class="about-section">
                            <div class="about-section-icon">
                                <svg width="48" height="48" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                </svg>
                            </div>
                            <h2>Our Mission</h2>
                            <p>We are committed to providing our customers with the best online shopping experience. Our mission is to offer a wide range of quality products at affordable prices, backed by excellent customer service and fast delivery across Nepal.</p>
                        </section>

                        <div class="about-features">
                            <div class="about-feature-card">
                                <div class="feature-icon">
                                    <svg width="32" height="32" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
                                    </svg>
                                </div>
                                <h3>Secure Shopping</h3>
                                <p>Your data and transactions are always protected with industry-standard security.</p>
                            </div>

                            <div class="about-feature-card">
                                <div class="feature-icon">
                                    <svg width="32" height="32" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                                    </svg>
                                </div>
                                <h3>Fast Delivery</h3>
                                <p>Quick and reliable delivery to all districts across Nepal.</p>
                            </div>

                            <div class="about-feature-card">
                                <div class="feature-icon">
                                    <svg width="32" height="32" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                                    </svg>
                                </div>
                                <h3>24/7 Support</h3>
                                <p>Our customer support team is always here to help you.</p>
                            </div>

                            <div class="about-feature-card">
                                <div class="feature-icon">
                                    <svg width="32" height="32" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M21 8V7l-3 2-3-2v1l3 2 3-2zm1-5H2C.9 3 0 3.9 0 5v14c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM8 6c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm6 12H2v-1c0-2 4-3.1 6-3.1s6 1.1 6 3.1v1zm8-6h-8V6h8v6z"/>
                                    </svg>
                                </div>
                                <h3>Member Benefits</h3>
                                <p>Registered users enjoy exclusive 2% discount on all orders.</p>
                            </div>
                        </div>

                        <section class="about-section about-values">
                            <h2>Why Choose Us?</h2>
                            <div class="values-list">
                                <div class="value-item">
                                    <span class="value-check">✓</span>
                                    <span>100% Genuine Products</span>
                                </div>
                                <div class="value-item">
                                    <span class="value-check">✓</span>
                                    <span>Best Prices Guaranteed</span>
                                </div>
                                <div class="value-item">
                                    <span class="value-check">✓</span>
                                    <span>Easy Returns & Refunds</span>
                                </div>
                                <div class="value-item">
                                    <span class="value-check">✓</span>
                                    <span>Cash on Delivery Available</span>
                                </div>
                                <div class="value-item">
                                    <span class="value-check">✓</span>
                                    <span>Nationwide Shipping</span>
                                </div>
                                <div class="value-item">
                                    <span class="value-check">✓</span>
                                    <span>Trusted by 50,000+ Customers</span>
                                </div>
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        `;
    }

    renderContactPage() {
        return `
            <div class="contact-page">
                <div class="contact-hero">
                    <div class="contact-hero-content">
                        <h1 class="contact-title">Contact Us</h1>
                        <p class="contact-tagline">We'd love to hear from you</p>
                    </div>
                    <div class="contact-hero-bg"></div>
                </div>

                <div class="container">
                    <div class="contact-content">
                        <div class="contact-info-section">
                            <div class="contact-card">
                                <div class="contact-card-icon">
                                    <svg width="40" height="40" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                                    </svg>
                                </div>
                                <h3>Our Location</h3>
                                <p class="contact-detail">Basundhara, Kathmandu</p>
                                <p class="contact-subdetail">Nepal</p>
                            </div>

                            <div class="contact-card">
                                <div class="contact-card-icon">
                                    <svg width="40" height="40" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/>
                                    </svg>
                                </div>
                                <h3>Phone Number</h3>
                                <p class="contact-detail">9824236055</p>
                                <p class="contact-subdetail">Available 10 AM - 6 PM</p>
                            </div>

                            <div class="contact-card">
                                <div class="contact-card-icon">
                                    <svg width="40" height="40" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                                    </svg>
                                </div>
                                <h3>Email Address</h3>
                                <p class="contact-detail">support@ovnstore.com</p>
                                <p class="contact-subdetail">We reply within 24 hours</p>
                            </div>

                            <div class="contact-card">
                                <div class="contact-card-icon">
                                    <svg width="40" height="40" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
                                    </svg>
                                </div>
                                <h3>Business Hours</h3>
                                <p class="contact-detail">Sun - Fri: 10 AM - 6 PM</p>
                                <p class="contact-subdetail">Saturday: Closed</p>
                            </div>
                        </div>

                        <div class="contact-form-section">
                            <div class="contact-form-card">
                                <h2>Send us a Message</h2>
                                <p class="form-subtitle">Have a question or feedback? We're here to help!</p>

                                <form class="contact-form" onsubmit="window.app.handleContactForm(event)">
                                    <div class="form-row">
                                        <div class="form-group">
                                            <label for="contact-name">Full Name</label>
                                            <input type="text" id="contact-name" name="name" placeholder="Enter your name" required>
                                        </div>
                                        <div class="form-group">
                                            <label for="contact-email">Email Address</label>
                                            <input type="email" id="contact-email" name="email" placeholder="Enter your email" required>
                                        </div>
                                    </div>

                                    <div class="form-group">
                                        <label for="contact-phone">Phone Number</label>
                                        <input type="tel" id="contact-phone" name="phone" placeholder="Enter your phone number">
                                    </div>

                                    <div class="form-group">
                                        <label for="contact-subject">Subject</label>
                                        <select id="contact-subject" name="subject" required>
                                            <option value="">Select a subject</option>
                                            <option value="general">General Inquiry</option>
                                            <option value="order">Order Related</option>
                                            <option value="product">Product Information</option>
                                            <option value="complaint">Complaint</option>
                                            <option value="feedback">Feedback</option>
                                            <option value="other">Other</option>
                                        </select>
                                    </div>

                                    <div class="form-group">
                                        <label for="contact-message">Your Message</label>
                                        <textarea id="contact-message" name="message" rows="5" placeholder="Write your message here..." required></textarea>
                                    </div>

                                    <button type="submit" class="contact-submit-btn">
                                        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                                        </svg>
                                        Send Message
                                    </button>
                                </form>
                            </div>
                        </div>

                        <div class="contact-map-section">
                            <h2>Find Us</h2>
                            <div class="map-placeholder">
                                <div class="map-content">
                                    <svg width="64" height="64" fill="#667eea" viewBox="0 0 24 24">
                                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                                    </svg>
                                    <h3>Basundhara, Kathmandu</h3>
                                    <p>Visit our store for a personalized shopping experience</p>
                                    <a href="https://maps.google.com/?q=Basundhara,Kathmandu,Nepal" target="_blank" class="map-link">
                                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/>
                                        </svg>
                                        Open in Google Maps
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async handleContactForm(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const submitBtn = form.querySelector('.contact-submit-btn');

        // Disable button during submission
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<svg class="animate-spin" width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2v4m0 12v4m-8-10H0m24 0h-4m-2.343-5.657l-2.829 2.829m-5.656 5.656l-2.829 2.829m11.314 0l-2.829-2.829M6.343 6.343L3.515 3.515"/></svg> Sending...';

        try {
            const response = await fetch(`${this.apiBase}/api/contact/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: formData.get('name'),
                    email: formData.get('email'),
                    phone: formData.get('phone') || '',
                    subject: formData.get('subject'),
                    message: formData.get('message')
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(data.message, 'success');
                form.reset();
            } else {
                this.showNotification(data.error || 'Failed to send message. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Contact form error:', error);
            this.showNotification('Failed to send message. Please try again.', 'error');
        } finally {
            // Re-enable button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg> Send Message';
        }
    }

    renderCartPage() {
        const total = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

        return `
            <div class="cart-page">
                <div class="container">
                    <div class="section-header">
                        <h2 class="section-title">Shopping Cart</h2>
                        <p class="section-subtitle">${this.cart.length} items in your cart</p>
                    </div>
                    
                    ${this.cart.length === 0 ? 
                        `<div class="empty-cart">
                            <h3>Your cart is empty</h3>
                            <p>Add some products to get started!</p>
                            <a href="/products" data-route="/products" class="cta-primary">Continue Shopping</a>
                        </div>` :
                        `<div class="cart-content">
                            <div class="cart-items">
                                ${this.cart.map(item => `
                                    <div class="cart-item" data-product-id="${item.id}">
                                        <img src="${item.image}" alt="${item.name}" class="cart-item-image">
                                        <div class="cart-item-details">
                                            <h3 class="cart-item-name">${item.name}</h3>
                                            <p class="cart-item-price">Rs ${item.price}</p>
                                            <div class="cart-item-controls">
                                                <button class="qty-btn qty-minus" onclick="window.app.updateCartQuantity(${item.id}, ${item.quantity - 1})">-</button>
                                                <span class="qty-display">${item.quantity}</span>
                                                <button class="qty-btn qty-plus" onclick="window.app.updateCartQuantity(${item.id}, ${item.quantity + 1})">+</button>
                                            </div>
                                        </div>
                                        <div class="cart-item-total">
                                            Rs ${(item.price * item.quantity).toFixed(2)}
                                        </div>
                                        <button class="remove-btn" onclick="window.app.removeFromCart(${item.id})">×</button>
                                    </div>
                                `).join('')}
                            </div>

                            <div class="cart-summary-section">
                                <div class="cart-summary-card">
                                    <h3 class="summary-title">Order Summary</h3>
                                    <div class="summary-row">
                                        <span>Subtotal</span>
                                        <span>Rs ${total.toFixed(2)}</span>
                                    </div>
                                    <div class="summary-row">
                                        <span>Shipping</span>
                                        <span class="shipping-calc">Calculated at checkout</span>
                                    </div>
                                    <div class="summary-divider"></div>
                                    <div class="summary-row total">
                                        <span>Total</span>
                                        <span>Rs ${total.toFixed(2)}</span>
                                    </div>
                                    <a href="/checkout" data-route="/checkout" class="checkout-btn cta-primary">
                                        Proceed to Checkout
                                        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/>
                                        </svg>
                                    </a>
                                    <div class="secure-checkout">
                                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
                                        </svg>
                                        <span>Secure checkout</span>
                                    </div>
                                </div>
                            </div>
                        </div>`
                    }
                </div>
            </div>
        `;
    }

    // ==========================================
    // PRODUCT DETAIL PAGE - Beautiful UI
    // ==========================================
    renderProductDetailPage(productId) {
        // Clean URL query params
        if (window.location.search) {
            window.history.replaceState({}, '', window.location.pathname);
        }

        const product = this.products.find(p => p.id == productId);

        if (!product) {
            return `
                <div class="product-not-found">
                    <div class="container">
                        <div class="not-found-content">
                            <div class="not-found-icon">
                                <svg width="120" height="120" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                            </div>
                            <h1>Product Not Found</h1>
                            <p>The product you're looking for doesn't exist or has been removed.</p>
                            <a href="/products" data-route="/products" class="cta-primary">Browse Products</a>
                        </div>
                    </div>
                </div>
            `;
        }

        // Calculate discount - works regardless of which field has higher value
        let discount = 0;
        if (product.compare_price && product.compare_price !== product.price) {
            const higher = Math.max(product.price, product.compare_price);
            const lower = Math.min(product.price, product.compare_price);
            discount = Math.round(((higher - lower) / higher) * 100);
        }
        const inCart = this.cart.find(item => item.id == productId);

        // Get related products sorted by CTR (most clicked first)
        const relatedProducts = this.products
            .filter(p => p.id !== product.id)
            .sort((a, b) => {
                const clicksA = this.productClicks[a.id] || 0;
                const clicksB = this.productClicks[b.id] || 0;
                return clicksB - clicksA;
            })
            .slice(0, 10);

        return `
            <div class="product-detail-page">
                <!-- Breadcrumb -->
                <div class="breadcrumb-section">
                    <div class="container">
                        <nav class="breadcrumb">
                            <a href="/" data-route="/">Home</a>
                            <span class="separator">
                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
                                </svg>
                            </span>
                            <a href="/products" data-route="/products">Products</a>
                            <span class="separator">
                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
                                </svg>
                            </span>
                            <span class="current">${product.name}</span>
                        </nav>
                    </div>
                </div>

                <!-- Main Product Section -->
                <section class="product-main-section">
                    <div class="container">
                        <div class="product-detail-grid">
                            <!-- Product Images -->
                            <div class="product-gallery">
                                <div class="main-image-container">
                                    ${discount > 0 ? `<div class="discount-badge">${discount}% OFF</div>` : ''}
                                    <img src="${product.image}" alt="${product.name}" class="main-product-image" id="mainProductImage">
                                    <div class="image-zoom-overlay">
                                        <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                                            <path d="M12 10h-2v2H9v-2H7V9h2V7h1v2h2v1z"/>
                                        </svg>
                                    </div>
                                </div>
                            </div>

                            <!-- Product Info -->
                            <div class="product-info-section">
                                <div class="product-badges">
                                    <span class="category-badge">${product.category}</span>
                                    ${product.stock_status === 'in_stock' ? '<span class="stock-badge in-stock">In Stock</span>' :
                                      product.stock_status === 'low_stock' ? '<span class="stock-badge low-stock">Low Stock</span>' :
                                      '<span class="stock-badge out-of-stock">Out of Stock</span>'}
                                </div>

                                <h1 class="product-title">${product.name}</h1>

                                <div class="product-rating-section">
                                    <div class="stars-display">
                                        ${this.renderStars(product.rating || 4.5)}
                                    </div>
                                    <span class="rating-value">${product.rating || 4.5}</span>
                                    <span class="reviews-count">(${product.reviews || 0} reviews)</span>
                                </div>

                                <div class="price-section">
                                    ${(() => {
                                        const price = product.price;
                                        const comparePrice = product.compare_price;

                                        // Format number with commas
                                        const formatPrice = (num) => {
                                            return num.toLocaleString('en-IN');
                                        };

                                        // Determine which is selling price and which is MRP
                                        if (comparePrice && comparePrice < price) {
                                            const discountPercent = Math.round(((price - comparePrice) / price) * 100);
                                            return `
                                                <span class="current-price">Rs. ${formatPrice(comparePrice)}</span>
                                                <span class="original-price-wrap">
                                                    <span class="original-price">Rs. ${formatPrice(price)}</span><sup class="discount-percent">-${discountPercent}%</sup>
                                                </span>
                                            `;
                                        } else if (comparePrice && comparePrice > price) {
                                            const discountPercent = Math.round(((comparePrice - price) / comparePrice) * 100);
                                            return `
                                                <span class="current-price">Rs. ${formatPrice(price)}</span>
                                                <span class="original-price-wrap">
                                                    <span class="original-price">Rs. ${formatPrice(comparePrice)}</span><sup class="discount-percent">-${discountPercent}%</sup>
                                                </span>
                                            `;
                                        } else {
                                            return `<span class="current-price">Rs. ${formatPrice(price)}</span>`;
                                        }
                                    })()}
                                </div>

                                <div class="product-description">
                                    <p>${product.description || product.short_description || 'Experience premium quality with this exceptional product. Crafted with attention to detail and designed for optimal performance.'}</p>
                                </div>

                                <!-- Quantity Selector -->
                                <div class="quantity-section">
                                    <label class="quantity-label">Quantity</label>
                                    <div class="quantity-selector">
                                        <button class="qty-btn minus" onclick="window.app.decrementDetailQty()">
                                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M19 13H5v-2h14v2z"/>
                                            </svg>
                                        </button>
                                        <input type="number" class="qty-input" id="productQty" value="1" min="1" max="10">
                                        <button class="qty-btn plus" onclick="window.app.incrementDetailQty()">
                                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                                            </svg>
                                        </button>
                                    </div>
                                </div>

                                <!-- Action Buttons -->
                                <div class="action-buttons">
                                    <button class="add-to-cart-btn primary ${product.stock_status === 'out_of_stock' ? 'disabled' : ''}"
                                            onclick="window.app.addToCartWithQty(${product.id})"
                                            ${product.stock_status === 'out_of_stock' ? 'disabled' : ''}>
                                        <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M11 9h2V6h3V4h-3V1h-2v3H8v2h3v3zm-4 9c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zm10 0c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2zm-9.83-3.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.86-7.01L19.42 4h-.01l-1.1 2-2.76 5H8.53l-.13-.27L6.16 6l-.95-2-.94-2H1v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25z"/>
                                        </svg>
                                        ${inCart ? 'Update' : 'Cart'}
                                    </button>
                                    <button class="buy-now-btn secondary" onclick="window.app.buyNow(${product.id})">
                                        <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
                                        </svg>
                                        Buy
                                    </button>
                                </div>

                                <!-- Product Features -->
                                <div class="product-features">
                                    <div class="feature-item">
                                        <div class="feature-icon">
                                            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                                            </svg>
                                        </div>
                                        <div class="feature-text">
                                            <strong>Free Delivery</strong>
                                            <span>On orders over Rs 1,000</span>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <div class="feature-icon">
                                            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M19 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.11 0 2-.9 2-2V5c0-1.1-.89-2-2-2zm-9 14l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                            </svg>
                                        </div>
                                        <div class="feature-text">
                                            <strong>Quality Guaranteed</strong>
                                            <span>100% authentic products</span>
                                        </div>
                                    </div>
                                    <div class="feature-item">
                                        <div class="feature-icon">
                                            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                                <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
                                            </svg>
                                        </div>
                                        <div class="feature-text">
                                            <strong>Easy Returns</strong>
                                            <span>14-day return policy</span>
                                        </div>
                                    </div>
                                </div>

                                ${product.sku ? `
                                    <div class="product-meta">
                                        <span class="meta-item"><strong>SKU:</strong> ${product.sku}</span>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Related Products -->
                ${relatedProducts.length > 0 ? `
                    <section class="related-products-section">
                        <div class="container">
                            <div class="section-header">
                                <h2 class="section-title">You May Also Like</h2>
                            </div>
                            <div class="related-products-scroll">
                                ${relatedProducts.map(p => this.renderRelatedProductCard(p)).join('')}
                            </div>
                        </div>
                    </section>
                ` : ''}

                <!-- Reviews Section -->
                <section class="reviews-section">
                    <div class="container">
                        <div class="section-header reviews-header">
                            <h2 class="section-title">Customer Reviews</h2>
                            <div id="writeReviewBtnContainer"></div>
                        </div>
                        <div id="reviewsContainer" data-product-id="${product.id}">
                            <div class="reviews-loading">
                                <div class="loading-spinner"></div>
                                <p>Loading reviews...</p>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        `;
    }

    // Load reviews after page render
    loadProductReviews(productId) {
        const container = document.getElementById('reviewsContainer');
        if (!container) return;

        fetch(`/api/products/api/${productId}/reviews/`, {
            credentials: 'include'
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.renderReviews(container, data, productId);
                } else {
                    container.innerHTML = '<p class="reviews-error">Unable to load reviews</p>';
                }
            })
            .catch(err => {
                console.error('Error loading reviews:', err);
                container.innerHTML = '<p class="reviews-error">Unable to load reviews</p>';
            });
    }

    renderReviews(container, data, productId) {
        const { reviews, total_reviews, average_rating, rating_distribution } = data;

        // Add Write Review button to header with subtitle below
        const btnContainer = document.getElementById('writeReviewBtnContainer');
        if (btnContainer) {
            btnContainer.innerHTML = `
                <div class="reviews-header-right">
                    <button class="btn-write-review" onclick="window.app.checkCanReview(${productId})">
                        <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                        </svg>
                        Write a Review
                    </button>
                    <p class="reviews-subtitle">See what our customers are saying</p>
                </div>
            `;
        }

        let html = `
            <div class="reviews-content">
                <!-- Write Review Form Container -->
                <div id="writeReviewSection" class="write-review-section"></div>

                <!-- Reviews Summary -->
                <div class="reviews-summary">
                    <div class="average-rating">
                        <div class="rating-number">${average_rating}</div>
                        <div class="rating-stars">${this.renderStars(average_rating)}</div>
                        <div class="total-reviews">Based on ${total_reviews} review${total_reviews !== 1 ? 's' : ''}</div>
                    </div>
                    <div class="rating-breakdown">
                        ${[5,4,3,2,1].map(star => `
                            <div class="rating-bar">
                                <span class="star-label">${star} star</span>
                                <div class="bar-container">
                                    <div class="bar-fill" style="width: ${total_reviews > 0 ? (rating_distribution[star] / total_reviews * 100) : 0}%"></div>
                                </div>
                                <span class="count">${rating_distribution[star]}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Reviews List -->
                <div class="reviews-list">
                    ${reviews.length > 0 ? reviews.map(review => `
                        <div class="review-card">
                            <div class="review-header">
                                <div class="reviewer-info">
                                    <div class="reviewer-avatar">${review.user.charAt(0).toUpperCase()}</div>
                                    <div class="reviewer-details">
                                        <div class="reviewer-name">${review.user}</div>
                                        <div class="review-date">${review.created_at}</div>
                                    </div>
                                    ${review.is_verified_purchase ? '<span class="verified-badge"><svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg> Verified Purchase</span>' : ''}
                                </div>
                                <div class="review-rating">${this.renderStars(review.rating)}</div>
                            </div>
                            ${review.title ? `<h4 class="review-title">${review.title}</h4>` : ''}
                            <p class="review-comment">${review.comment}</p>
                            ${review.images && review.images.length > 0 ? `
                                <div class="review-images">
                                    ${review.images.map(img => `
                                        <a href="${img.url}" target="_blank" class="review-image">
                                            <img src="${img.url}" alt="${img.alt || 'Review image'}">
                                        </a>
                                    `).join('')}
                                </div>
                            ` : ''}
                            ${review.admin_response ? `
                                <div class="admin-response">
                                    <div class="response-header">
                                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
                                        </svg>
                                        Store Response
                                    </div>
                                    <p>${review.admin_response}</p>
                                </div>
                            ` : ''}
                            <div class="review-footer">
                                <button class="helpful-btn" onclick="window.app.markHelpful(${review.id})">
                                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/>
                                    </svg>
                                    Helpful (${review.helpful_count})
                                </button>
                            </div>
                        </div>
                    `).join('') : `
                        <div class="no-reviews">
                            <svg width="64" height="64" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                            </svg>
                            <h3>No Reviews Yet</h3>
                            <p>Be the first to share your experience with this product!</p>
                        </div>
                    `}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    checkCanReview(productId) {
        console.log('checkCanReview called for product:', productId);
        // Let the server check if user is logged in
        fetch(`/api/products/api/${productId}/can-review/`, {
            credentials: 'include'
        })
            .then(res => res.json())
            .then(data => {
                console.log('can-review response:', data);
                if (data.success) {
                    if (data.can_review) {
                        console.log('Showing review form with order_id:', data.order_id);
                        this.showReviewForm(productId, data.order_id);
                    } else {
                        if (data.reason === 'login_required') {
                            this.showNotification(data.message, 'warning');
                            this.navigate('/login');
                        } else if (data.reason === 'already_reviewed') {
                            this.showNotification(data.message, 'info');
                        } else if (data.reason === 'no_purchase') {
                            this.showNotification(data.message, 'warning');
                        } else {
                            this.showNotification(data.message || 'Cannot review this product', 'warning');
                        }
                    }
                } else {
                    this.showNotification(data.error || 'Error checking review eligibility', 'error');
                }
            })
            .catch(err => {
                console.error('Error checking review eligibility:', err);
                this.showNotification('Error checking review eligibility', 'error');
            });
    }

    showReviewForm(productId, orderId) {
        const section = document.getElementById('writeReviewSection');
        if (!section) return;

        section.innerHTML = `
            <div class="review-form-container">
                <h3>Write Your Review</h3>
                <form id="reviewForm" onsubmit="window.app.submitReview(event, ${productId}, '${orderId}')">
                    <div class="form-group">
                        <label>Your Rating *</label>
                        <div class="star-rating-input">
                            ${[5,4,3,2,1].map(n => `
                                <input type="radio" name="rating" id="star${n}" value="${n}" ${n === 5 ? 'checked' : ''}>
                                <label for="star${n}" class="star-label">★</label>
                            `).join('')}
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Your Review *</label>
                        <textarea name="comment" class="form-control" rows="4" required placeholder="Tell us about your experience with this product..." minlength="10"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Add Photos (Optional)</label>
                        <div class="image-upload-area">
                            <input type="file" id="reviewImages" accept="image/*" multiple onchange="window.app.previewReviewImages(this)">
                            <div class="upload-placeholder">
                                <svg width="32" height="32" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M19 7v2.99s-1.99.01-2 0V7h-3s.01-1.99 0-2h3V2h2v3h3v2h-3zm-3 4V8h-3V5H5c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-8h-3zM5 19l3-4 2 3 3-4 4 5H5z"/>
                                </svg>
                                <span>Click to upload images (max 5)</span>
                            </div>
                            <div id="imagePreview" class="image-preview"></div>
                        </div>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn-secondary" onclick="window.app.cancelReviewForm(${productId})">Cancel</button>
                        <button type="submit" class="btn-primary">Submit Review</button>
                    </div>
                </form>
            </div>
        `;
    }

    previewReviewImages(input) {
        const preview = document.getElementById('imagePreview');
        if (!preview) return;

        const files = Array.from(input.files).slice(0, 5);
        preview.innerHTML = '';

        files.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const div = document.createElement('div');
                div.className = 'preview-image';
                div.innerHTML = `
                    <img src="${e.target.result}" alt="Preview">
                    <button type="button" class="remove-preview" onclick="window.app.removePreviewImage(${index})">&times;</button>
                `;
                preview.appendChild(div);
            };
            reader.readAsDataURL(file);
        });
    }

    removePreviewImage(index) {
        const input = document.getElementById('reviewImages');
        const preview = document.getElementById('imagePreview');
        if (!input || !preview) return;

        // Can't modify FileList directly, so we clear and show message
        const items = preview.querySelectorAll('.preview-image');
        if (items[index]) {
            items[index].remove();
        }
    }

    cancelReviewForm(productId) {
        const section = document.getElementById('writeReviewSection');
        if (section) {
            section.innerHTML = `
                <button class="btn-write-review" onclick="window.app.checkCanReview(${productId})">
                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                    </svg>
                    Write a Review
                </button>
            `;
        }
    }

    async submitReview(event, productId, orderId) {
        event.preventDefault();

        const form = event.target;
        const formData = new FormData(form);

        const rating = formData.get('rating');
        const title = formData.get('title');
        const comment = formData.get('comment');

        if (!comment || comment.trim().length < 10) {
            this.showNotification('Please write at least 10 characters for your review', 'warning');
            return;
        }

        // Get images as base64
        const imageInput = document.getElementById('reviewImages');
        const images = [];
        if (imageInput && imageInput.files.length > 0) {
            const files = Array.from(imageInput.files).slice(0, 5);
            for (const file of files) {
                const base64 = await this.fileToBase64(file);
                images.push(base64);
            }
        }

        const reviewData = {
            rating: parseInt(rating),
            title: title || '',
            comment: comment,
            order_id: orderId,
            images: images
        };

        // Get CSRF token
        const getCookie = (name) => {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        };
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                          getCookie('csrftoken');

        fetch(`/api/products/api/${productId}/submit-review/`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(reviewData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                this.showNotification(data.message, 'success');
                // Reload reviews
                this.loadProductReviews(productId);
            } else {
                this.showNotification(data.error || 'Failed to submit review', 'error');
            }
        })
        .catch(err => {
            console.error('Error submitting review:', err);
            this.showNotification('Error submitting review', 'error');
        });
    }

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }

    markHelpful(reviewId) {
        this.showNotification('Thanks for your feedback!', 'success');
    }

    renderStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalf = rating % 1 >= 0.5;
        let stars = '';

        for (let i = 0; i < 5; i++) {
            if (i < fullStars) {
                stars += '<span class="star filled">★</span>';
            } else if (i === fullStars && hasHalf) {
                stars += '<span class="star half">★</span>';
            } else {
                stars += '<span class="star">★</span>';
            }
        }
        return stars;
    }

    decrementDetailQty() {
        const input = document.getElementById('productQty');
        if (input && parseInt(input.value) > 1) {
            input.value = parseInt(input.value) - 1;
        }
    }

    incrementDetailQty() {
        const input = document.getElementById('productQty');
        if (input && parseInt(input.value) < 10) {
            input.value = parseInt(input.value) + 1;
        }
    }

    addToCartWithQty(productId) {
        const input = document.getElementById('productQty');
        const qty = input ? parseInt(input.value) : 1;

        const product = this.products.find(p => p.id == productId);
        if (!product) return;

        const existingItem = this.cart.find(item => item.id == productId);
        if (existingItem) {
            existingItem.quantity = qty;
        } else {
            this.cart.push({
                id: product.id,
                name: product.name,
                price: product.price,
                image: product.image,
                quantity: qty
            });
        }

        localStorage.setItem('cart', JSON.stringify(this.cart));
        this.showNotification(`${product.name} added to cart!`, 'success');
        this.renderApp();
    }

    buyNow(productId) {
        this.addToCartWithQty(productId);
        setTimeout(() => {
            this.navigate('/checkout');
        }, 300);
    }


    // ==========================================
    // CHECKOUT PAGE - Simple Single Panel
    // ==========================================
    renderCheckoutPage() {
        if (this.cart.length === 0) {
            return `
                <div class="checkout-empty">
                    <div style="text-align: center; padding: 60px 20px;">
                        <svg width="80" height="80" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" style="margin-bottom: 20px;">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
                        </svg>
                        <h2 style="color: #1f2937; margin-bottom: 10px;">Your Cart is Empty</h2>
                        <p style="color: #64748b; margin-bottom: 20px;">Add some products to your cart before checkout</p>
                        <a href="/products" data-route="/products" class="btn-primary-admin">Browse Products</a>
                    </div>
                </div>
            `;
        }

        const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

        // Build location options - combining district and location like admin panel
        const locationOptions = NEPAL_DELIVERY_RATES.map(loc =>
            `<option value="${loc.district} - ${loc.location}" data-rate="${loc.rate}">${loc.district} - ${loc.location}</option>`
        ).join('');

        return `
            <div class="admin-checkout-page">
                <!-- Page Header -->
                <div class="page-header">
                    <h1 class="page-title">Checkout</h1>
                    <div style="margin-top: 12px;">
                        <a href="/cart" data-route="/cart" class="btn btn-secondary">
                            <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
                            </svg>
                            Back to Cart
                        </a>
                    </div>
                </div>

                <form id="checkoutForm" onsubmit="window.app.submitOrder(event)">
                    <div class="checkout-grid-admin">
                        <!-- Left Side - Form Fields -->
                        <div class="checkout-left">
                            <!-- Customer Details -->
                            <div class="data-table">
                                <div class="table-header">
                                    <h3 class="table-title">
                                        <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                                        </svg>
                                        Customer Details
                                    </h3>
                                </div>
                                <div style="padding: 20px;">
                                    <div class="form-grid-2">
                                        <div class="form-group">
                                            <label class="form-label">Customer Name *</label>
                                            <input type="text" name="customer_name" class="form-control" required
                                                   placeholder="Enter full name" value="${this.currentUser?.first_name || ''}">
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">Contact Number *</label>
                                            <input type="tel" name="contact_number" class="form-control" required
                                                   placeholder="10 digit number" pattern="[0-9]{10}" maxlength="10"
                                                   oninput="this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10)">
                                        </div>
                                    </div>
                                    <div class="form-grid-2">
                                        <div class="form-group">
                                            <label class="form-label">District / Location *</label>
                                            <select name="location" id="locationSelect" class="form-control" required
                                                    onchange="window.app.onLocationChange()">
                                                <option value="">-- Select Location --</option>
                                                ${locationOptions}
                                            </select>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">Landmark / Address Detail</label>
                                            <input type="text" name="landmark" class="form-control"
                                                   placeholder="Street, Near...">
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Products -->
                            <div class="data-table">
                                <div class="table-header">
                                    <h3 class="table-title">
                                        <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-7-2h2v-4h4v-2h-4V7h-2v4H8v2h4z"/>
                                        </svg>
                                        Products
                                    </h3>
                                </div>
                                <div style="padding: 20px;">
                                    <div id="orderItems">
                                        ${this.cart.map(item => `
                                            <div class="order-item-row-admin">
                                                <div class="product-info-admin">
                                                    <div class="product-image-admin">
                                                        <img src="${item.image}" alt="${item.name}">
                                                    </div>
                                                    <div class="product-details-admin">
                                                        <div class="product-name-admin">${item.name}</div>
                                                        <div class="product-price-admin">Rs ${item.price}</div>
                                                    </div>
                                                </div>
                                                <div class="product-controls-admin">
                                                    <div class="control-group-admin">
                                                        <label>Qty</label>
                                                        <div class="qty-display">${item.quantity}</div>
                                                    </div>
                                                    <div class="control-group-admin">
                                                        <label>Total</label>
                                                        <div class="line-total-admin">Rs ${item.price * item.quantity}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            </div>

                            <!-- Payment Method -->
                            <div class="data-table">
                                <div class="table-header">
                                    <h3 class="table-title">
                                        <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/>
                                        </svg>
                                        Payment
                                    </h3>
                                </div>
                                <div style="padding: 20px;">
                                    <div class="form-group">
                                        <label class="form-label">Payment Method *</label>
                                        <div class="payment-grid-admin">
                                            <label class="payment-option-admin selected">
                                                <input type="radio" name="payment_method" value="cod" checked>
                                                <span>
                                                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                                        <path d="M2 7h20v10H2V7zm10 2c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm-7 1c0 1.1-.9 2-2 2v2c1.1 0 2 .9 2 2h14c0-1.1.9-2 2-2v-2c-1.1 0-2-.9-2-2H5z"/>
                                                    </svg>
                                                    COD
                                                </span>
                                            </label>
                                            <label class="payment-option-admin">
                                                <input type="radio" name="payment_method" value="esewa">
                                                <span>
                                                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                                        <path d="M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z"/>
                                                    </svg>
                                                    eSewa
                                                </span>
                                            </label>
                                            <label class="payment-option-admin">
                                                <input type="radio" name="payment_method" value="khalti">
                                                <span>
                                                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                                        <path d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                                                    </svg>
                                                    Khalti
                                                </span>
                                            </label>
                                            <label class="payment-option-admin">
                                                <input type="radio" name="payment_method" value="imepay">
                                                <span>
                                                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                                        <path d="M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14zm-4.2-5.78v1.75l3.2-2.99-3.2-2.99v1.7c-3.18.26-4.86 1.94-5.18 4.53 1.17-1.45 2.76-2.09 5.18-2z"/>
                                                    </svg>
                                                    IME Pay
                                                </span>
                                            </label>
                                            <label class="payment-option-admin">
                                                <input type="radio" name="payment_method" value="bank">
                                                <span>
                                                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                                        <path d="M4 10h3v7H4zm6.5 0h3v7h-3zM2 19h20v3H2zm15-9h3v7h-3zm-5-9L2 6v2h20V6z"/>
                                                    </svg>
                                                    Bank
                                                </span>
                                            </label>
                                        </div>
                                    </div>
                                    <div class="form-group" style="margin-top: 16px;">
                                        <label class="form-label">Order Notes</label>
                                        <textarea name="notes" class="form-control" rows="2"
                                                  placeholder="Any special instructions..."></textarea>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Right Side - Order Summary -->
                        <div class="checkout-right">
                            <div class="data-table sticky-card">
                                <div class="table-header">
                                    <h3 class="table-title">
                                        <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l4.59-4.58L18 11l-6 6z"/>
                                        </svg>
                                        Order Summary
                                    </h3>
                                </div>
                                <div style="padding: 20px;">
                                    <!-- Items Summary -->
                                    <div id="itemsSummary" class="items-summary-admin">
                                        ${this.cart.map(item => `
                                            <div class="summary-item">
                                                <span>${item.name} x${item.quantity}</span>
                                                <span>Rs ${item.price * item.quantity}</span>
                                            </div>
                                        `).join('')}
                                    </div>

                                    <hr class="summary-divider">

                                    <!-- Totals -->
                                    <div class="totals-section">
                                        <div class="total-row">
                                            <span class="total-label">Subtotal:</span>
                                            <span id="subtotalDisplay">Rs ${subtotal}</span>
                                        </div>
                                        <div class="total-row">
                                            <span class="total-label">Delivery (0.5kg rate):</span>
                                            <span id="deliveryDisplay" class="delivery-amount">Rs 0</span>
                                        </div>
                                        <div class="total-row discount-row" id="discountRow" style="display: none; color: #10b981;">
                                            <span class="total-label">Member Discount (2%):</span>
                                            <span id="discountDisplay">- Rs 0</span>
                                        </div>
                                        <input type="hidden" name="delivery_charge" id="deliveryCharge" value="0">
                                        <hr class="summary-divider-thick">
                                        <div class="total-row grand-total">
                                            <strong>Total:</strong>
                                            <strong id="totalDisplay" class="total-amount">Rs ${subtotal}</strong>
                                        </div>
                                        <div id="loginPromo" class="login-promo" style="margin-top: 12px; padding: 10px; background: #fef3c7; border-radius: 8px; font-size: 13px; display: none;">
                                            <span style="color: #92400e;">💡 Login to get <strong>2% discount</strong> on your order!</span>
                                        </div>
                                    </div>

                                    <!-- Location Info -->
                                    <div id="locationInfo" class="location-info-box" style="display: none;">
                                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M18 18.5c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5-1.5.67-1.5 1.5.67 1.5 1.5 1.5zM19.5 9.5h-3V12h4.46l-1.46-2.5zM6 18.5c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5-1.5.67-1.5 1.5.67 1.5 1.5 1.5zM20 8l3 4v5h-2c0 1.66-1.34 3-3 3s-3-1.34-3-3H9c0 1.66-1.34 3-3 3s-3-1.34-3-3H1V6c0-1.11.89-2 2-2h14v4h3z"/>
                                        </svg>
                                        <span>Delivery to: <strong id="selectedLocation">-</strong></span>
                                    </div>

                                    <!-- Submit Button -->
                                    <button type="submit" class="btn btn-primary btn-submit-order" style="width: 100%; justify-content: center; padding: 14px; margin-top: 20px; font-size: 16px;">
                                        <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                                        </svg>
                                        Place Order
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        `;
    }

    // Handle location change - same as admin panel
    onLocationChange() {
        const select = document.getElementById('locationSelect');
        const rate = select.options[select.selectedIndex]?.dataset?.rate || 0;
        const locationText = select.options[select.selectedIndex]?.text?.trim() || '';

        document.getElementById('deliveryCharge').value = rate;
        document.getElementById('deliveryDisplay').textContent = 'Rs ' + rate;

        if (parseInt(rate) > 0) {
            document.getElementById('locationInfo').style.display = 'flex';
            document.getElementById('selectedLocation').textContent = locationText;
        } else {
            document.getElementById('locationInfo').style.display = 'none';
        }

        this.updateOrderTotal();
    }

    // Update order total with discount calculation
    updateOrderTotal() {
        const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const delivery = parseInt(document.getElementById('deliveryCharge')?.value || 0);

        // Calculate discount if logged in
        const discountPercent = this.isLoggedIn ? 2 : 0;
        const discount = Math.round(subtotal * discountPercent / 100);
        const total = subtotal + delivery - discount;

        document.getElementById('subtotalDisplay').textContent = 'Rs ' + subtotal;
        document.getElementById('totalDisplay').textContent = 'Rs ' + total;

        // Show/hide discount row
        const discountRow = document.getElementById('discountRow');
        const discountDisplay = document.getElementById('discountDisplay');
        const loginPromo = document.getElementById('loginPromo');

        if (this.isLoggedIn && discount > 0) {
            if (discountRow) {
                discountRow.style.display = 'flex';
                discountDisplay.textContent = '- Rs ' + discount;
            }
            if (loginPromo) loginPromo.style.display = 'none';
        } else {
            if (discountRow) discountRow.style.display = 'none';
            if (loginPromo) loginPromo.style.display = 'block';
        }
    }

    // Check login status for discount
    async checkLoginStatus() {
        try {
            const response = await fetch('/orders/api/check-login/', {
                credentials: 'same-origin'
            });
            const data = await response.json();
            this.isLoggedIn = data.is_logged_in;
            this.discountPercent = data.discount_percent;
            console.log('Login status:', this.isLoggedIn, 'Discount:', this.discountPercent + '%');

            // Update the total if on checkout page
            if (window.location.pathname === '/checkout') {
                this.updateOrderTotal();
            }
        } catch (error) {
            console.error('Failed to check login status:', error);
            this.isLoggedIn = false;
            this.discountPercent = 0;
        }
    }

    // Get unique list of Nepal districts
    getNepalDistricts() {
        const districts = [...new Set(NEPAL_DELIVERY_RATES.map(item => item.district))];
        return districts.sort();
    }

    // Get locations for a specific district
    getLocationsForDistrict(district) {
        return NEPAL_DELIVERY_RATES
            .filter(item => item.district === district)
            .map(item => ({ location: item.location, rate: item.rate }));
    }

    // Update location dropdown when district changes
    updateLocations() {
        const districtSelect = document.getElementById('district');
        const locationSelect = document.getElementById('location');
        const district = districtSelect.value;

        // Clear current locations
        locationSelect.innerHTML = '<option value="">Select Location</option>';

        if (district) {
            const locations = this.getLocationsForDistrict(district);
            locations.forEach(loc => {
                const option = document.createElement('option');
                option.value = loc.location;
                option.textContent = `${loc.location} (Rs ${loc.rate})`;
                option.dataset.rate = loc.rate;
                locationSelect.appendChild(option);
            });
        }

        // Reset shipping display
        this.updateShipping();
    }

    // Calculate shipping based on selected location
    calculateShipping(location) {
        if (!location) return 0;

        // Find the rate for the selected location
        const rateEntry = NEPAL_DELIVERY_RATES.find(item => item.location === location);
        return rateEntry ? rateEntry.rate : 150; // Default rate if not found
    }

    // Update shipping display when location changes
    updateShipping() {
        const locationSelect = document.getElementById('location');
        const location = locationSelect ? locationSelect.value : '';
        const subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const shipping = this.calculateShipping(location);
        const total = subtotal + shipping;

        const shippingLine = document.getElementById('shippingLine');
        const totalAmount = document.getElementById('totalAmount');

        if (shippingLine) {
            if (!location) {
                shippingLine.innerHTML = `
                    <span>Shipping</span>
                    <span class="select-location-hint">Select location</span>
                `;
            } else {
                shippingLine.innerHTML = `
                    <span>Shipping</span>
                    <span>Rs ${shipping.toFixed(2)}</span>
                `;
            }
        }

        if (totalAmount) {
            totalAmount.textContent = `Rs ${total.toFixed(2)}`;
        }
    }

    selectPaymentOption(input) {
        document.querySelectorAll('.payment-option').forEach(el => el.classList.remove('selected'));
        input.closest('.payment-option').classList.add('selected');
    }

    async submitOrder(e) {
        e.preventDefault();
        console.log('submitOrder called');

        const form = document.getElementById('checkoutForm');

        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const btn = document.querySelector('.btn-submit-order');
        if (!btn) {
            console.error('Submit button not found');
            return;
        }

        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="loading-spinner"></span> Processing...';
        btn.disabled = true;

        try {
            // Collect form data
            const formData = new FormData(form);
            const customerName = formData.get('customer_name');
            const contactNumber = formData.get('contact_number');
            const location = formData.get('location');
            const landmark = formData.get('landmark') || '';
            const paymentMethod = formData.get('payment_method');
            const notes = formData.get('notes') || '';

            // Get delivery charge from the hidden input field
            const deliveryCharge = parseFloat(document.getElementById('deliveryCharge')?.value || 0);

            // Prepare cart items
            const items = this.cart.map(item => ({
                product_id: item.id,
                quantity: item.quantity
            }));

            // Send order to backend
            const response = await fetch('/orders/api/create/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    customer_name: customerName,
                    contact_number: contactNumber,
                    location: location,
                    landmark: landmark,
                    payment_method: paymentMethod,
                    notes: notes,
                    delivery_charge: deliveryCharge,
                    items: items
                })
            });

            const result = await response.json();
            console.log('Order API response:', result);

            if (result.success) {
                // Clear cart
                this.cart = [];
                localStorage.removeItem('cart');
                this.checkoutData = null;

                this.showNotification('Order placed successfully!', 'success');
                this.navigate(`/order-confirmation/${result.order_number}`);
            } else {
                throw new Error(result.error || 'Failed to place order');
            }
        } catch (error) {
            console.error('Order error:', error);
            this.showNotification(error.message || 'Failed to place order. Please try again.', 'error');
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }

    // ==========================================
    // ORDER CONFIRMATION PAGE
    // ==========================================
    renderOrderConfirmationPage(orderId) {
        return `
            <div class="order-confirmation-page">
                <div class="container">
                    <div class="confirmation-content">
                        <div class="success-animation">
                            <div class="checkmark-circle">
                                <svg class="checkmark" width="80" height="80" viewBox="0 0 52 52">
                                    <circle class="checkmark-circle-bg" cx="26" cy="26" r="25" fill="none"/>
                                    <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                                </svg>
                            </div>
                        </div>

                        <h1 class="confirmation-title">Order Confirmed!</h1>
                        <p class="confirmation-subtitle">Thank you for shopping with OVN Store</p>

                        <div class="order-details-card">
                            <div class="order-id-section">
                                <span class="label">Order ID</span>
                                <span class="order-id">#${orderId}</span>
                            </div>

                            <div class="confirmation-info">
                                <div class="info-item">
                                    <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                                    </svg>
                                    <div>
                                        <strong>Confirmation Email Sent</strong>
                                        <p>Check your inbox for order details</p>
                                    </div>
                                </div>
                                <div class="info-item">
                                    <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4z"/>
                                    </svg>
                                    <div>
                                        <strong>Estimated Delivery</strong>
                                        <p>3-5 business days</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="confirmation-actions">
                            <a href="/products" data-route="/products" class="btn-primary">
                                Continue Shopping
                                <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/>
                                </svg>
                            </a>
                            <button class="btn-secondary" onclick="window.print()">
                                <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V3z"/>
                                </svg>
                                Print Receipt
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // ==========================================
    // MY ORDERS PAGE
    // ==========================================
    renderOrdersPage() {
        // Load orders when page renders
        setTimeout(() => this.loadUserOrders(), 100);

        return `
            <div class="my-orders-page">
                <div class="container">
                    <!-- Page Header -->
                    <div class="orders-page-header">
                        <div class="header-content">
                            <h1>My Orders</h1>
                            <p>Track your orders and write reviews for delivered items</p>
                        </div>
                        <a href="/products" data-route="/products" class="continue-shopping-btn">
                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                            </svg>
                            Continue Shopping
                        </a>
                    </div>

                    <div id="ordersContainer">
                        <div class="orders-loading">
                            <div class="loading-spinner"></div>
                            <p>Loading your orders...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async loadUserOrders() {
        try {
            const response = await fetch('/orders/api/my-orders/', {
                credentials: 'same-origin'
            });
            const data = await response.json();

            const container = document.getElementById('ordersContainer');
            if (!container) return;

            if (!data.success || data.orders.length === 0) {
                container.innerHTML = `
                    <div class="empty-orders-state">
                        <div class="empty-icon">
                            <svg width="80" height="80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/>
                            </svg>
                        </div>
                        <h2>No Orders Yet</h2>
                        <p>Looks like you haven't placed any orders yet. Start shopping to see your orders here!</p>
                        <a href="/products" data-route="/products" class="shop-now-btn">
                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                            </svg>
                            Start Shopping
                        </a>
                    </div>
                `;
                return;
            }

            // Group orders by status
            const delivered = data.orders.filter(o => o.status === 'delivered');
            const active = data.orders.filter(o => !['delivered', 'cancelled', 'returned'].includes(o.status));
            const other = data.orders.filter(o => ['cancelled', 'returned'].includes(o.status));

            container.innerHTML = `
                <!-- Order Stats -->
                <div class="order-stats">
                    <div class="stat-card">
                        <div class="stat-icon total">
                            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l4.59-4.58L18 11l-6 6z"/>
                            </svg>
                        </div>
                        <div class="stat-info">
                            <span class="stat-number">${data.orders.length}</span>
                            <span class="stat-label">Total Orders</span>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon active">
                            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                            </svg>
                        </div>
                        <div class="stat-info">
                            <span class="stat-number">${active.length}</span>
                            <span class="stat-label">In Progress</span>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon delivered">
                            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                            </svg>
                        </div>
                        <div class="stat-info">
                            <span class="stat-number">${delivered.length}</span>
                            <span class="stat-label">Delivered</span>
                        </div>
                    </div>
                </div>

                <!-- Active Orders -->
                ${active.length > 0 ? `
                    <div class="orders-section">
                        <h2 class="section-title">
                            <span class="title-dot active"></span>
                            Active Orders
                        </h2>
                        <div class="orders-grid">
                            ${active.map(order => this.renderOrderCard(order)).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Delivered Orders -->
                ${delivered.length > 0 ? `
                    <div class="orders-section">
                        <h2 class="section-title">
                            <span class="title-dot delivered"></span>
                            Delivered Orders
                            <span class="review-hint">You can write reviews for these orders!</span>
                        </h2>
                        <div class="orders-grid">
                            ${delivered.map(order => this.renderOrderCard(order, true)).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Cancelled/Returned Orders -->
                ${other.length > 0 ? `
                    <div class="orders-section">
                        <h2 class="section-title">
                            <span class="title-dot cancelled"></span>
                            Cancelled / Returned
                        </h2>
                        <div class="orders-grid">
                            ${other.map(order => this.renderOrderCard(order)).join('')}
                        </div>
                    </div>
                ` : ''}
            `;
        } catch (error) {
            console.error('Failed to load orders:', error);
            const container = document.getElementById('ordersContainer');
            if (container) {
                container.innerHTML = `
                    <div class="error-state">
                        <svg width="64" height="64" fill="none" viewBox="0 0 24 24" stroke="#ef4444">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                        </svg>
                        <p>Failed to load orders. Please try again.</p>
                        <button onclick="window.app.loadUserOrders()" class="retry-btn">Retry</button>
                    </div>
                `;
            }
        }
    }

    renderOrderCard(order, canReview = false) {
        const statusConfig = {
            'pending': { color: '#d97706', bg: '#fef3c7' },
            'processing': { color: '#2563eb', bg: '#dbeafe' },
            'confirmed': { color: '#3b82f6', bg: '#dbeafe' },
            'packed': { color: '#8b5cf6', bg: '#ede9fe' },
            'shipped': { color: '#4f46e5', bg: '#e0e7ff' },
            'delivered': { color: '#16a34a', bg: '#dcfce7' },
            'cancelled': { color: '#dc2626', bg: '#fee2e2' },
            'returned': { color: '#ca8a04', bg: '#fef3c7' }
        };

        const status = statusConfig[order.status] || statusConfig['processing'];

        return `
            <div class="order-card-new">
                <div class="order-card-header">
                    <div class="order-id-date">
                        <span class="order-number">#${order.order_number}</span>
                        <span class="order-date">${order.created_at}</span>
                    </div>
                    <span class="order-status-badge" style="background: ${status.bg}; color: ${status.color};">
                        ${order.status_display}
                    </span>
                </div>

                <div class="order-items-preview">
                    ${order.items.slice(0, 2).map(item => `
                        <div class="item-preview">
                            <div class="item-image">
                                ${item.product_image ?
                                    `<img src="${item.product_image}" alt="${item.product_name}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                     <div class="no-image" style="display:none;"><svg width="24" height="24" fill="#94a3b8" viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg></div>` :
                                    `<div class="no-image"><svg width="24" height="24" fill="#94a3b8" viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg></div>`
                                }
                            </div>
                            <div class="item-info">
                                <span class="item-name">${item.product_name}</span>
                                <div class="item-price-qty">
                                    <span class="item-unit-price">Rs ${item.unit_price || item.total_price}</span>
                                    <span class="item-qty-badge">${item.quantity} pcs</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                    ${order.items.length > 2 ? `
                        <div class="more-items">+${order.items.length - 2} more item${order.items.length - 2 > 1 ? 's' : ''}</div>
                    ` : ''}
                </div>

                <div class="order-card-footer">
                    <div class="order-total">
                        <span class="total-label">TOTAL</span>
                        <span class="total-amount">Rs ${order.total_amount}</span>
                    </div>
                    <div class="order-actions">
                        ${canReview ? `
                            <button class="review-btn" onclick="window.app.openOrderReviewModal('${order.order_id}', ${JSON.stringify(order.items).replace(/"/g, '&quot;')})">
                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
                                </svg>
                                Write Review
                            </button>
                        ` : ''}
                        <a href="/my-orders/${order.order_id}" data-route="/my-orders/${order.order_id}" class="view-details-btn">
                            View Details
                            <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
                            </svg>
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    openOrderReviewModal(orderId, items) {
        // Parse items if it's a string
        if (typeof items === 'string') {
            items = JSON.parse(items.replace(/&quot;/g, '"'));
        }

        // If only one product, go directly to review
        if (items.length === 1 && items[0].product_id) {
            this.selectProductForReview(items[0].product_id, items[0].product_name, orderId);
            return;
        }

        // If multiple products, show selection modal
        const modalHtml = `
            <div class="review-modal-overlay" id="orderReviewModal" onclick="if(event.target === this) window.app.closeOrderReviewModal()">
                <div class="review-modal">
                    <div class="review-modal-header">
                        <h2>Write a Review</h2>
                        <button class="close-modal-btn" onclick="window.app.closeOrderReviewModal()">
                            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="review-modal-body">
                        <p class="modal-subtitle">Select a product to review:</p>
                        <div class="review-products-list">
                            ${items.map(item => `
                                <div class="review-product-item" onclick="window.app.selectProductForReview(${item.product_id}, '${item.product_name.replace(/'/g, "\\'")}', '${orderId}')">
                                    <div class="product-thumb">
                                        ${item.product_image ?
                                            `<img src="${item.product_image}" alt="${item.product_name}">` :
                                            `<div class="no-thumb"><svg width="24" height="24" fill="#94a3b8" viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg></div>`
                                        }
                                    </div>
                                    <div class="product-details">
                                        <span class="product-name">${item.product_name}</span>
                                    </div>
                                    <svg class="arrow-icon" width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
                                    </svg>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        document.body.style.overflow = 'hidden';

        // Add active class after a small delay for animation
        setTimeout(() => {
            const modal = document.getElementById('orderReviewModal');
            if (modal) {
                modal.classList.add('active');
            }
        }, 10);
    }

    closeOrderReviewModal() {
        const modal = document.getElementById('orderReviewModal');
        if (modal) {
            modal.remove();
            document.body.style.overflow = '';
        }
    }

    selectProductForReview(productId, productName, orderId) {
        this.closeOrderReviewModal();
        // Navigate to product page with review section
        this.navigate(`/product/${productId}`);
        // Trigger review form after navigation
        setTimeout(() => {
            this.checkCanReview(productId);
        }, 500);
    }

    // ==========================================
    // ORDER DETAIL PAGE
    // ==========================================
    renderOrderDetailPage(orderId) {
        // Load order details when page renders
        setTimeout(() => this.loadOrderDetail(orderId), 100);

        return `
            <div class="order-detail-page-new">
                <div class="detail-page-header">
                    <a href="/my-orders" data-route="/my-orders" class="back-to-orders">
                        <i class="fas fa-arrow-left"></i>
                        <span>Back to My Orders</span>
                    </a>
                    <h1><i class="fas fa-file-invoice"></i> Order Details</h1>
                </div>
                <div id="orderDetailContainer">
                    <div class="detail-loading">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Loading order details...</p>
                    </div>
                </div>
            </div>
        `;
    }

    async loadOrderDetail(orderId) {
        try {
            const response = await fetch(`/orders/api/${orderId}/`, {
                credentials: 'same-origin'
            });
            const data = await response.json();

            const container = document.getElementById('orderDetailContainer');
            if (!container) return;

            if (!data.success) {
                container.innerHTML = `
                    <div class="detail-error-state">
                        <i class="fas fa-exclamation-circle"></i>
                        <h3>Order Not Found</h3>
                        <p>${data.error || 'The order you are looking for does not exist.'}</p>
                        <a href="/my-orders" data-route="/my-orders" class="back-link">
                            <i class="fas fa-arrow-left"></i> Go back to orders
                        </a>
                    </div>
                `;
                return;
            }

            const order = data.order;

            // Status configuration
            const statusConfig = {
                'pending': { icon: 'clock', color: '#d97706', bg: '#fef3c7' },
                'processing': { icon: 'cog', color: '#2563eb', bg: '#dbeafe' },
                'confirmed': { icon: 'check-circle', color: '#3b82f6', bg: '#dbeafe' },
                'packed': { icon: 'box', color: '#8b5cf6', bg: '#ede9fe' },
                'shipped': { icon: 'truck', color: '#4f46e5', bg: '#e0e7ff' },
                'delivered': { icon: 'check-double', color: '#16a34a', bg: '#dcfce7' },
                'cancelled': { icon: 'times-circle', color: '#dc2626', bg: '#fee2e2' },
                'returned': { icon: 'undo', color: '#ca8a04', bg: '#fef3c7' }
            };
            const statusInfo = statusConfig[order.status] || { icon: 'question', color: '#6b7280', bg: '#f3f4f6' };

            // Progress steps
            const orderSteps = ['pending', 'processing', 'confirmed', 'packed', 'shipped', 'delivered'];
            const currentStepIndex = orderSteps.indexOf(order.status);
            const isCancelled = order.status === 'cancelled' || order.status === 'returned';

            container.innerHTML = `
                <div class="order-detail-content">
                    <!-- Order Status Card -->
                    <div class="detail-status-card">
                        <div class="status-card-header">
                            <div class="order-id-info">
                                <span class="label">Order Number</span>
                                <h2>#${order.order_number}</h2>
                            </div>
                            <div class="current-status" style="background: ${statusInfo.bg}; color: ${statusInfo.color};">
                                <i class="fas fa-${statusInfo.icon}"></i>
                                ${order.status_display}
                            </div>
                        </div>

                        ${!isCancelled ? `
                        <div class="order-progress">
                            ${orderSteps.map((step, index) => `
                                <div class="progress-step ${index <= currentStepIndex ? 'completed' : ''} ${index === currentStepIndex ? 'current' : ''}">
                                    <div class="step-dot">
                                        ${index < currentStepIndex ? '<i class="fas fa-check"></i>' : (index + 1)}
                                    </div>
                                    <span class="step-label">${step.charAt(0).toUpperCase() + step.slice(1)}</span>
                                </div>
                                ${index < orderSteps.length - 1 ? '<div class="progress-line ' + (index < currentStepIndex ? 'completed' : '') + '"></div>' : ''}
                            `).join('')}
                        </div>
                        ` : ''}

                        <div class="order-meta-grid">
                            <div class="meta-item">
                                <i class="fas fa-calendar"></i>
                                <div>
                                    <span class="label">Order Date</span>
                                    <span class="value">${order.created_at}</span>
                                </div>
                            </div>
                            <div class="meta-item">
                                <i class="fas fa-credit-card"></i>
                                <div>
                                    <span class="label">Payment</span>
                                    <span class="value">${order.payment_method.toUpperCase()}</span>
                                </div>
                            </div>
                            <div class="meta-item">
                                <i class="fas fa-${order.payment_status === 'paid' ? 'check-circle' : 'clock'}"></i>
                                <div>
                                    <span class="label">Payment Status</span>
                                    <span class="value ${order.payment_status === 'paid' ? 'paid' : 'pending'}">${order.payment_status_display}</span>
                                </div>
                            </div>
                            ${order.tracking_number ? `
                            <div class="meta-item">
                                <i class="fas fa-shipping-fast"></i>
                                <div>
                                    <span class="label">Tracking #</span>
                                    <span class="value">${order.tracking_number}</span>
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>

                    <div class="detail-grid">
                        <!-- Left Column -->
                        <div class="detail-left-col">
                            <!-- Order Items -->
                            <div class="detail-card">
                                <div class="card-header">
                                    <h3><i class="fas fa-shopping-bag"></i> Order Items</h3>
                                    <span class="item-count">${order.items.length} item${order.items.length > 1 ? 's' : ''}</span>
                                </div>
                                <div class="order-items-list">
                                    ${order.items.map(item => `
                                        <div class="order-item-row">
                                            <div class="item-thumb">
                                                ${item.product_image ?
                                                    `<img src="${item.product_image}" alt="${item.product_name}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                                     <div class="thumb-placeholder" style="display:none;"><i class="fas fa-image"></i></div>` :
                                                    `<div class="thumb-placeholder"><i class="fas fa-image"></i></div>`
                                                }
                                            </div>
                                            <div class="item-details">
                                                <h4>${item.product_name}</h4>
                                                <div class="item-meta-row">
                                                    <span class="item-sku">SKU: ${item.product_sku}</span>
                                                    <span class="item-qty-badge">${item.quantity} pcs</span>
                                                </div>
                                            </div>
                                            <div class="item-pricing">
                                                <span class="unit-price">Rs ${item.unit_price} x ${item.quantity}</span>
                                                <span class="total-price">Rs ${item.total_price || (item.unit_price * item.quantity)}</span>
                                            </div>
                                            ${order.status === 'delivered' && item.product_id ? `
                                                <button class="item-review-btn" onclick="app.selectProductForReview(${item.product_id})">
                                                    <i class="fas fa-star"></i> Review
                                                </button>
                                            ` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>

                            <!-- Order Timeline -->
                            ${order.history && order.history.length > 0 ? `
                            <div class="detail-card">
                                <div class="card-header">
                                    <h3><i class="fas fa-history"></i> Order Timeline</h3>
                                </div>
                                <div class="order-timeline">
                                    ${order.history.map((h, index) => `
                                        <div class="timeline-item ${index === 0 ? 'latest' : ''}">
                                            <div class="timeline-dot"></div>
                                            <div class="timeline-content">
                                                <div class="timeline-header">
                                                    <span class="action">${h.action}</span>
                                                    <span class="time">${h.created_at}</span>
                                                </div>
                                                ${h.note ? `<p class="timeline-note">${h.note}</p>` : ''}
                                                ${h.old_value && h.new_value ? `<p class="timeline-change"><span>${h.old_value}</span> <i class="fas fa-arrow-right"></i> <span>${h.new_value}</span></p>` : ''}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            ` : ''}
                        </div>

                        <!-- Right Column -->
                        <div class="detail-right-col">
                            <!-- Shipping Address -->
                            <div class="detail-card">
                                <div class="card-header">
                                    <h3><i class="fas fa-map-marker-alt"></i> Shipping Address</h3>
                                </div>
                                <div class="address-content">
                                    <p>${order.shipping_address.replace(/\n/g, '<br>')}</p>
                                </div>
                            </div>

                            <!-- Order Notes -->
                            ${order.notes ? `
                            <div class="detail-card">
                                <div class="card-header">
                                    <h3><i class="fas fa-sticky-note"></i> Order Notes</h3>
                                </div>
                                <div class="notes-content">
                                    <p>${order.notes}</p>
                                </div>
                            </div>
                            ` : ''}

                            <!-- Order Summary -->
                            <div class="detail-card summary-card">
                                <div class="card-header">
                                    <h3><i class="fas fa-receipt"></i> Order Summary</h3>
                                </div>
                                <div class="summary-content">
                                    <div class="summary-row">
                                        <span>Subtotal</span>
                                        <span>Rs ${order.subtotal}</span>
                                    </div>
                                    <div class="summary-row">
                                        <span>Shipping</span>
                                        <span>Rs ${order.shipping_cost}</span>
                                    </div>
                                    ${order.discount_amount > 0 ? `
                                    <div class="summary-row discount">
                                        <div>
                                            <span>Discount (2%)</span>
                                            <small>Registered user benefit</small>
                                        </div>
                                        <span>- Rs ${order.discount_amount}</span>
                                    </div>
                                    ` : ''}
                                    <div class="summary-divider"></div>
                                    <div class="summary-row total">
                                        <span>Total</span>
                                        <span>Rs ${order.total_amount}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Failed to load order detail:', error);
            const container = document.getElementById('orderDetailContainer');
            if (container) {
                container.innerHTML = `
                    <div class="detail-error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Something went wrong</h3>
                        <p>Failed to load order details. Please try again.</p>
                        <a href="/my-orders" data-route="/my-orders" class="back-link">
                            <i class="fas fa-arrow-left"></i> Go back to orders
                        </a>
                    </div>
                `;
            }
        }
    }

    initializeInteractiveComponents() {
        // Initialize any dynamic components after render
        this.setupFormValidation();
        this.setupAnimations();

        // Load reviews if on product detail page
        const reviewsContainer = document.getElementById('reviewsContainer');
        if (reviewsContainer) {
            const productId = reviewsContainer.dataset.productId;
            if (productId) {
                this.loadProductReviews(productId);
            }
        }
    }

    setupFormValidation() {
        const forms = document.querySelectorAll('.modern-login-form');
        forms.forEach(form => {
            const inputs = form.querySelectorAll('.field-input-modern, .input-clean');
            inputs.forEach(input => {
                input.addEventListener('blur', () => this.validateField(input));
                input.addEventListener('input', () => this.clearFieldError(input));
            });
        });

        // Enhanced UX for new clean forms
        this.setupPasswordToggle();
        this.setupFormAnimations();
    }

    setupPasswordToggle() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.password-toggle-clean')) {
                const toggle = e.target.closest('.password-toggle-clean');
                const input = toggle.closest('.input-group-clean').querySelector('.input-clean');
                
                if (input.type === 'password') {
                    input.type = 'text';
                    toggle.innerHTML = `
                        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                        </svg>
                    `;
                } else {
                    input.type = 'password';
                    toggle.innerHTML = `
                        <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                        </svg>
                    `;
                }
            }
        });
    }

    setupFormAnimations() {
        // Add loading state to submit buttons
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.login-form-clean, .register-form-clean')) {
                const submitBtn = e.target.querySelector('.submit-btn-clean');
                if (submitBtn) {
                    submitBtn.classList.add('loading');
                    
                    // Remove loading state after processing (simulated)
                    setTimeout(() => {
                        submitBtn.classList.remove('loading');
                    }, 2000);
                }
            }
        });

        // Enhanced input focus effects
        document.addEventListener('focus', (e) => {
            if (e.target.matches('.input-clean')) {
                e.target.closest('.input-group-clean').classList.add('focused');
            }
        }, true);

        document.addEventListener('blur', (e) => {
            if (e.target.matches('.input-clean')) {
                e.target.closest('.input-group-clean').classList.remove('focused');
            }
        }, true);
    }

    validateField(input) {
        const value = input.value.trim();
        const errorEl = input.parentElement.querySelector('.field-error-modern');
        
        if (!value && input.required) {
            this.showFieldError(input, 'This field is required');
            return false;
        }
        
        if (input.type === 'email' && value && !this.isValidEmail(value)) {
            this.showFieldError(input, 'Please enter a valid email address');
            return false;
        }
        
        this.clearFieldError(input);
        return true;
    }

    showFieldError(input, message) {
        const errorEl = input.parentElement.querySelector('.field-error-modern');
        if (errorEl) {
            errorEl.textContent = message;
            input.classList.add('error');
        }
    }

    clearFieldError(input) {
        const errorEl = input.parentElement.querySelector('.field-error-modern');
        if (errorEl) {
            errorEl.textContent = '';
            input.classList.remove('error');
        }
    }

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    setupAnimations() {
        // Add scroll animations and other interactive effects
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        const animateElements = document.querySelectorAll('.product-card, .category-card, .section-header');
        animateElements.forEach(el => observer.observe(el));
    }

    // Cart functionality
    addToCart(productId) {
        const product = this.products.find(p => p.id == productId);
        if (!product) return;

        const existingItem = this.cart.find(item => item.id == productId);
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({
                id: product.id,
                name: product.name,
                price: product.price,
                image: product.image,
                quantity: 1
            });
        }

        localStorage.setItem('cart', JSON.stringify(this.cart));
        this.showNotification('Product added to cart!', 'success');
        this.renderApp();
    }

    buyNow(productId) {
        const product = this.products.find(p => p.id == productId);
        if (!product) return;

        // Clear cart and add only this product
        this.cart = [{
            id: product.id,
            name: product.name,
            price: product.price,
            image: product.image,
            quantity: 1
        }];

        localStorage.setItem('cart', JSON.stringify(this.cart));
        this.navigate('/checkout');
    }

    updateCartQuantity(productId, newQuantity) {
        if (newQuantity <= 0) {
            this.removeFromCart(productId);
            return;
        }

        const item = this.cart.find(item => item.id == productId);
        if (item) {
            item.quantity = newQuantity;
            localStorage.setItem('cart', JSON.stringify(this.cart));
            this.renderApp();
        }
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.id != productId);
        localStorage.setItem('cart', JSON.stringify(this.cart));
        this.showNotification('Product removed from cart', 'info');
        this.renderApp();
    }

    toggleCart() {
        this.navigate('/cart');
    }

    // ============================================
    // FAST SEARCH FUNCTIONALITY
    // ============================================

    handleSearch(query) {
        this.searchQuery = query;

        if (!query.trim()) {
            this.searchResults = [];
            this.isSearching = false;
            this.hideSearchDropdown();
            return;
        }

        // Use debounced search for performance
        this.debouncedSearch(query);
    }

    // Perform the actual search using the search engine
    performSearch(query) {
        if (!query.trim()) {
            this.hideSearchDropdown();
            return;
        }

        this.isSearching = true;

        // Use fast Trie + fuzzy search
        const results = searchEngine.search(query, 8);
        this.searchResults = results;
        this.selectedSearchIndex = -1;

        // Render the dropdown
        this.showSearchDropdown(results, query);

        this.isSearching = false;
    }

    // Show search results dropdown
    showSearchDropdown(results, query) {
        const container = document.querySelector('.search-container');
        if (!container) return;

        // Remove existing dropdown
        const existingDropdown = container.querySelector('.search-dropdown');
        if (existingDropdown) existingDropdown.remove();

        // Create dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'search-dropdown';

        if (results.length === 0) {
            dropdown.innerHTML = `
                <div class="search-no-results">
                    <svg width="40" height="40" fill="#9ca3af" viewBox="0 0 24 24">
                        <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                    </svg>
                    <p>No products found for "${this.escapeHtml(query)}"</p>
                    <span>Try a different search term</span>
                </div>
            `;
        } else {
            const resultsHtml = results.map((product, index) => {
                const highlightedName = this.highlightMatch(product.name, query);
                const price = parseFloat(product.price) || 0;

                return `
                    <div class="search-result-item" data-product-id="${product.id}" data-index="${index}">
                        <div class="search-result-image">
                            ${product.image ?
                                `<img src="${product.image}" alt="${this.escapeHtml(product.name)}">` :
                                `<div class="search-result-placeholder">
                                    <svg width="24" height="24" fill="#9ca3af" viewBox="0 0 24 24">
                                        <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
                                    </svg>
                                </div>`
                            }
                        </div>
                        <div class="search-result-info">
                            <div class="search-result-name">${highlightedName}</div>
                            <div class="search-result-meta">
                                <span class="search-result-category">${this.escapeHtml(product.category || 'Uncategorized')}</span>
                                <span class="search-result-price">Rs. ${price.toLocaleString()}</span>
                            </div>
                        </div>
                        <div class="search-result-arrow">
                            <svg width="16" height="16" fill="#9ca3af" viewBox="0 0 24 24">
                                <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
                            </svg>
                        </div>
                    </div>
                `;
            }).join('');

            dropdown.innerHTML = `
                <div class="search-results-list">
                    ${resultsHtml}
                </div>
            `;
        }

        container.appendChild(dropdown);
        this.searchDropdownVisible = true;

        // Add click handlers to results
        dropdown.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const productId = item.dataset.productId;
                this.hideSearchDropdown();
                this.navigate(`/product/${productId}`);
            });
        });

    }

    // Hide search dropdown
    hideSearchDropdown() {
        const dropdown = document.querySelector('.search-dropdown');
        if (dropdown) {
            dropdown.classList.add('hiding');
            setTimeout(() => dropdown.remove(), 150);
        }
        this.searchDropdownVisible = false;
        this.selectedSearchIndex = -1;
    }

    // Update visual selection in dropdown
    updateSearchSelection(items) {
        items.forEach((item, index) => {
            if (index === this.selectedSearchIndex) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('selected');
            }
        });
    }

    // Highlight matching text in search results
    highlightMatch(text, query) {
        if (!query.trim()) return this.escapeHtml(text);

        const escapedText = this.escapeHtml(text);
        const queryWords = query.toLowerCase().split(/\s+/);
        let result = escapedText;

        queryWords.forEach(word => {
            if (word.length >= 2) {
                const regex = new RegExp(`(${this.escapeRegex(word)})`, 'gi');
                result = result.replace(regex, '<mark>$1</mark>');
            }
        });

        return result;
    }

    // Escape HTML special characters
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Escape regex special characters
    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Notification system
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Authentication handlers
    async handleLogin(form) {
        try {
            const formData = new FormData(form);
            const username = formData.get('username');
            const password = formData.get('password');

            if (!username || !password) {
                this.showNotification('Please enter both username and password', 'error');
                return;
            }

            this.showNotification('Signing in...', 'info');

            // Call the API login endpoint
            const response = await fetch(`${this.apiBase}/api/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Important: include cookies
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (data.success) {
                // Store user info
                this.currentUser = data.user;
                localStorage.setItem('currentUser', JSON.stringify(this.currentUser));

                this.showNotification(data.message, 'success');

                // Check for redirect URL or if user is admin
                const urlParams = new URLSearchParams(window.location.search);
                const nextUrl = urlParams.get('next');

                setTimeout(() => {
                    if (nextUrl) {
                        // Redirect to the specified URL
                        window.location.href = nextUrl;
                    } else {
                        // Always go to home - user can click Admin Dashboard if needed
                        this.navigate('/');
                    }
                }, 1000);
            } else {
                this.showNotification(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Login failed. Please try again.', 'error');
        }
    }

    async handleGoogleLogin() {
        try {
            this.showNotification('Connecting to Google...', 'info');
            
            if (!this.googleAuth.isInitialized) {
                await this.googleAuth.init();
            }
            
            const result = await this.googleAuth.signIn();

            // Handle redirect flow - the page will redirect to Google
            if (result.redirecting) {
                this.showNotification('Redirecting to Google...', 'info');
                return; // Page will redirect, nothing more to do
            }

            if (result.success && result.idToken) {
                // Send token to backend for authentication
                console.log('📤 Sending token to backend...', {
                    hasIdToken: !!result.idToken,
                    hasAccessToken: !!result.accessToken,
                    userEmail: result.user?.email
                });
                this.showNotification('Authenticating with server...', 'info');
                
                try {
                    const response = await fetch(`${this.apiBase}/api/google-auth/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        credentials: 'include',
                        body: JSON.stringify({
                            idToken: result.idToken,
                            accessToken: result.accessToken || result.idToken
                        })
                    });
                    
                    console.log('📥 Backend response status:', response.status);
                    
                    const data = await response.json();
                    console.log('📥 Backend response data:', data);
                    
                    if (data.success) {
                        // Store user info with backend data
                        this.currentUser = {
                            ...data.user,
                            login_method: 'google',
                            picture: data.user.picture || result.user.picture
                        };
                        localStorage.setItem('currentUser', JSON.stringify(this.currentUser));

                        console.log('User logged in:', this.currentUser);

                        this.showNotification(data.message, 'success');

                        // Check for redirect URL
                        const urlParams = new URLSearchParams(window.location.search);
                        const nextUrl = urlParams.get('next');

                        setTimeout(() => {
                            if (nextUrl) {
                                window.location.href = nextUrl;
                            } else {
                                // Always go to home - user can click Admin Dashboard if needed
                                this.navigate('/');
                            }
                        }, 1000);
                    } else {
                        console.error('❌ Backend auth failed:', data);
                        this.showNotification('Authentication failed: ' + data.error, 'error');
                    }
                } catch (error) {
                    console.error('❌ Backend authentication error:', error);
                    this.showNotification('Failed to authenticate with server: ' + error.message, 'error');
                }
            } else if (result.cancelled) {
                this.showNotification('Sign-in cancelled. Please try again.', 'info');
            } else if (result.blocked) {
                this.showNotification('Popup was blocked. Please allow popups and try again.', 'error');
            } else if (result.config_needed) {
                this.showNotification('⚙️ Google OAuth needs configuration. Contact admin or check console for setup instructions.', 'error');
                console.error('═══════════════════════════════════════════════');
                console.error('🔧 GOOGLE OAUTH CONFIGURATION REQUIRED');
                console.error('═══════════════════════════════════════════════');
                console.error('The popup closes immediately because Google OAuth');
                console.error('is not configured for localhost:8000');
                console.error('');
                console.error('📋 TO FIX:');
                console.error('1. Go to: https://console.cloud.google.com/apis/credentials');
                console.error('2. Edit OAuth 2.0 Client ID: 735742648650-...');
                console.error('3. Add to "Authorized JavaScript origins":');
                console.error('   - http://localhost:8000');
                console.error('   - http://127.0.0.1:8000');
                console.error('4. Save and wait 5 minutes');
                console.error('5. Try login again');
                console.error('');
                console.error('See README.md for Google OAuth setup instructions');
                console.error('═══════════════════════════════════════════════');
            } else {
                this.showNotification(result.error || 'Google sign-in failed. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Google login error:', error);
            this.showNotification('Google login failed. Please try again.', 'error');
        }
    }

    async goToAdminDashboard() {
        try {
            // First, check if session is valid by making an API call
            const response = await fetch(`${this.apiBase}/api/auth-status/`, {
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.authenticated && (data.user.is_staff || data.user.is_superuser)) {
                // Session is valid, navigate to dashboard
                window.location.href = `${this.apiBase}/dashboard/`;
            } else {
                this.showNotification('Please login again to access admin panel', 'error');
                this.navigate('/login');
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            // Try to navigate anyway, backend will handle redirect
            window.location.href = `${this.apiBase}/dashboard/`;
        }
    }

    async handleLogout() {
        try {
            if (this.currentUser && this.currentUser.login_method === 'google') {
                await this.googleAuth.signOut();
            }
            await this.api.logout();
            
            this.currentUser = null;
            localStorage.removeItem('currentUser');
            
            this.showNotification('Successfully logged out', 'success');
            this.navigate('/');
        } catch (error) {
            console.error('Logout error:', error);
            this.showNotification('Logout failed', 'error');
        }
    }

    async handleNewsletterSignup(form) {
        const email = form.querySelector('input[type="email"]').value;
        
        if (!this.isValidEmail(email)) {
            this.showNotification('Please enter a valid email address', 'error');
            return;
        }

        try {
            // Here you would make an API call to subscribe the user
            this.showNotification('Thank you for subscribing!', 'success');
            form.reset();
        } catch (error) {
            this.showNotification('Subscription failed. Please try again.', 'error');
        }
    }
}

// Initialize the application
if (document.readyState === 'loading') {
    // DOM is still loading
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new ECommerceApp();
    });
} else {
    // DOM already loaded
    window.app = new ECommerceApp();
}