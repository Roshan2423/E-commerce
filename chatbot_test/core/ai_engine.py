"""
AI Engine for OVN Store Chatbot
Uses Groq API with Llama 3.3 for natural language understanding
Enhanced with Chain-of-Thought reasoning for smarter responses
"""
import json
import re
from typing import Dict, List, Optional, Any
from groq import Groq
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GROQ_API_KEY, GROQ_MODEL, STORE_INFO

# Try to import fast model, fallback to main model
try:
    from config import GROQ_MODEL_FAST
except ImportError:
    GROQ_MODEL_FAST = GROQ_MODEL


class AIEngine:
    """
    Groq-powered AI engine with Chain-of-Thought reasoning.
    Provides intelligent, context-aware responses that solve user problems.
    """

    SYSTEM_PROMPT = f"""You are OVN Store's intelligent AI shopping assistant. You THINK step-by-step before responding.

🏪 STORE INFORMATION:
- Store Name: {STORE_INFO['name']}
- Free shipping on orders above Rs. {STORE_INFO['free_shipping_threshold']}
- {STORE_INFO['return_days']}-day return policy for unused items
- Payment: Cash on Delivery only
- Delivery: {STORE_INFO['delivery_days']} business days across Nepal

🧠 YOUR THINKING PROCESS (use this for every response):
1. UNDERSTAND: What is the user actually asking/wanting?
2. ANALYZE: What information do I have? What's missing?
3. PLAN: What's the best way to help them?
4. RESPOND: Give a clear, helpful answer

💪 YOUR CAPABILITIES:
- Help find and recommend products
- Track orders (by order ID or phone number)
- Place orders through conversation
- Handle complaints, returns, and support issues
- Provide product information and reviews
- Answer policy questions

📝 RESPONSE STYLE:
- Be warm, friendly, and professional
- Keep responses concise but complete
- Use emojis sparingly for friendliness
- Never make up information (prices, order numbers, etc.)
- If unsure, ask for clarification
- Always try to SOLVE the user's problem, not just acknowledge it

🔧 PROBLEM-SOLVING APPROACH:
When a user has an issue:
1. Acknowledge their concern
2. Ask for needed information (order ID, phone, etc.)
3. Provide a solution or next steps
4. Confirm they're satisfied

❌ NEVER:
- Make up order numbers or tracking info
- Invent product prices or details
- Promise things outside store policy
- Leave problems unresolved

🎭 HANDLING OFF-TOPIC QUESTIONS:
When users ask questions unrelated to shopping (like weather, news, personal advice, etc.):
1. Be friendly and acknowledge their question
2. Politely explain you're specialized in shopping assistance
3. Offer to help with what you CAN do
4. Keep it brief and redirect to shopping

Example off-topic response:
"That's an interesting question! 😊 I'm specialized in helping you shop at OVN Store.
I can help you find products, place orders, or track deliveries. What would you like to do?"

🧩 FOR UNUSUAL/COMPLEX QUESTIONS:
1. Don't panic - think step by step
2. Identify what the user really needs
3. If related to shopping/orders - help them
4. If completely off-topic - politely redirect
5. Always be helpful and friendly
"""

    THINKING_PROMPT = """Before responding, think through this step by step:

<thinking>
1. What does the user want?
2. What context do I have?
3. What's the best response?
</thinking>

Now respond naturally (don't show the thinking tags to user):"""

    # Simple intents that don't need AI
    SIMPLE_INTENTS = ['greeting', 'thanks', 'bye', 'policy']

    def __init__(self, api_key: str = None):
        self.api_key = api_key or GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = GROQ_MODEL
        self.model_fast = GROQ_MODEL_FAST

    def is_available(self) -> bool:
        """Check if AI engine is available"""
        return self.client is not None and bool(self.api_key)

    def generate_response(
        self,
        user_message: str,
        context: Dict = None,
        conversation_history: List[Dict] = None,
        intent: str = None,
        products: List[Dict] = None,
        fast_mode: bool = True
    ) -> str:
        """
        Generate an intelligent AI response.
        Uses fast mode by default for quicker responses.
        """
        if not self.is_available():
            return self._fallback_response(intent, products)

        # Skip AI for simple intents - respond instantly
        if intent in self.SIMPLE_INTENTS:
            return self._fallback_response(intent, products)

        try:
            # Use fast mode for most queries
            if fast_mode:
                return self._generate_fast_response(user_message, context, intent, products)
            else:
                return self._generate_full_response(user_message, context, conversation_history, intent, products)

        except Exception as e:
            print(f"AI Engine error: {e}")
            return self._fallback_response(intent, products)

    def _generate_fast_response(
        self,
        user_message: str,
        context: Dict = None,
        intent: str = None,
        products: List[Dict] = None
    ) -> str:
        """Quick response using fast model - no chain-of-thought"""
        try:
            # Simple, direct prompt
            simple_prompt = f"""You are OVN Store's shopping assistant. Be brief and helpful.
Store: Free shipping above Rs.1000, 7-day returns, Cash on Delivery, 3-5 day delivery in Nepal.

User: {user_message}

Respond in 1-2 sentences. Be friendly. Use emojis."""

            response = self.client.chat.completions.create(
                model=self.model_fast,
                messages=[{"role": "user", "content": simple_prompt}],
                max_tokens=150,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Fast response error: {e}")
            return self._fallback_response(intent, products)

    def _generate_full_response(
        self,
        user_message: str,
        context: Dict = None,
        conversation_history: List[Dict] = None,
        intent: str = None,
        products: List[Dict] = None
    ) -> str:
        """Full response with chain-of-thought for complex queries"""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Add context information
        context_info = self._build_context_info(context, intent, products)
        if context_info:
            messages.append({
                "role": "system",
                "content": f"📋 CURRENT CONTEXT:\n{context_info}"
            })

        # Add conversation history (limited)
        if conversation_history:
            for msg in conversation_history[-4:]:  # Reduced from 6 to 4
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role in ['user', 'assistant'] and content:
                    messages.append({"role": role, "content": content})

        # Add thinking prompt + user message
        enhanced_message = f"{self.THINKING_PROMPT}\n\nUser: {user_message}"
        messages.append({"role": "user", "content": enhanced_message})

        # Call Groq API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=300,  # Reduced from 500
            temperature=0.7,
            top_p=0.9
        )

        result = response.choices[0].message.content.strip()
        return self._clean_response(result)

    def solve_problem(
        self,
        problem: str,
        context: Dict = None,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Dedicated problem-solving method that thinks through issues step by step.
        Returns both the solution and the reasoning.
        """
        if not self.is_available():
            return {
                "solution": "I'd be happy to help! Could you please provide more details?",
                "needs_info": True,
                "suggested_action": "ask_details"
            }

        try:
            problem_solving_prompt = f"""You are a problem-solving assistant. Analyze this customer issue step by step.

CUSTOMER ISSUE: "{problem}"

CONTEXT: {json.dumps(context) if context else "No additional context"}

Think through this carefully:

1. PROBLEM IDENTIFICATION:
   - What exactly is the issue?
   - Is this about: order, product, payment, delivery, return, or general inquiry?

2. INFORMATION CHECK:
   - What info do I already have?
   - What info do I need from the customer?

3. SOLUTION:
   - What's the best way to resolve this?
   - What are the next steps?

4. RESPONSE:
   - How should I communicate this to the customer?

Respond with JSON:
{{
    "problem_type": "order/product/delivery/payment/return/general",
    "understood_issue": "brief description of the issue",
    "needs_more_info": true/false,
    "info_needed": ["list of info needed if any"],
    "solution": "the solution or next steps",
    "response": "friendly response to customer",
    "suggested_action": "track_order/place_order/contact_support/provide_info/none"
}}"""

            messages = [
                {"role": "system", "content": "You are a problem-solving AI. Always respond with valid JSON."},
                {"role": "user", "content": problem_solving_prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.5
            )

            result_text = response.choices[0].message.content.strip()

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                return json.loads(json_match.group())

            return {
                "solution": result_text,
                "needs_info": False,
                "suggested_action": "none"
            }

        except Exception as e:
            print(f"Problem solving error: {e}")
            return {
                "solution": "I understand you have a concern. Let me help you with that.",
                "needs_info": True,
                "suggested_action": "ask_details"
            }

    def classify_intent(self, message: str, history: List[Dict] = None) -> Dict:
        """
        Fast intent classification using quick model.
        """
        if not self.is_available():
            return {"intent": "general", "confidence": 0.5}

        try:
            # Simple, fast prompt for intent classification
            prompt = f"""Classify this message into ONE category:
"{message}"

Categories: order_tracking, order_placement, support, review_view, review_submit, product_search, flash_sale, greeting, policy, thanks, bye, general

Reply with JSON only: {{"intent": "category", "confidence": 0.X}}"""

            response = self.client.chat.completions.create(
                model=self.model_fast,  # Use fast model
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,  # Minimal tokens
                temperature=0.2  # More deterministic
            )

            result_text = response.choices[0].message.content.strip()

            # Extract JSON
            json_match = re.search(r'\{[\s\S]*?\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "intent": result.get("intent", "general"),
                    "confidence": result.get("confidence", 0.7)
                }

            return {"intent": "general", "confidence": 0.5}

        except Exception as e:
            print(f"Intent classification error: {e}")
            return {"intent": "general", "confidence": 0.5}

    def understand_query(self, message: str, context: Dict = None) -> Dict:
        """
        Deep understanding of user query - extracts entities and intent.
        """
        if not self.is_available():
            return {"understood": False}

        try:
            prompt = f"""Analyze this customer message deeply.

MESSAGE: "{message}"

Extract:
1. Main intent (what they want to do)
2. Entities (product names, order IDs, phone numbers, etc.)
3. Sentiment (positive, negative, neutral)
4. Urgency (high, medium, low)
5. What action should the bot take?

Respond with JSON:
{{
    "intent": "main intent",
    "entities": {{
        "product": "product name if mentioned",
        "order_id": "order ID if mentioned",
        "phone": "phone number if mentioned",
        "quantity": number if mentioned
    }},
    "sentiment": "positive/negative/neutral",
    "urgency": "high/medium/low",
    "action": "suggested bot action",
    "summary": "brief summary of what user wants"
}}"""

            messages = [
                {"role": "system", "content": "You analyze customer messages. Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )

            result_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                return json.loads(json_match.group())

            return {"understood": False}

        except Exception as e:
            print(f"Query understanding error: {e}")
            return {"understood": False}

    def enhance_response(self, base_response: str, context: Dict = None) -> str:
        """
        Enhance a handler-generated response to be more natural and helpful.
        """
        if not self.is_available() or not base_response:
            return base_response

        try:
            prompt = f"""Improve this chatbot response to be more natural and helpful.

ORIGINAL: "{base_response}"

Rules:
- Keep all important information
- Make it conversational and friendly
- Add appropriate emoji if it helps
- Keep it concise (max 2-3 sentences)
- Don't add information that wasn't there

Improved response:"""

            messages = [
                {"role": "system", "content": "You improve chatbot responses to be natural and friendly."},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception:
            return base_response

    def _build_context_info(self, context: Dict, intent: str, products: List[Dict]) -> str:
        """Build rich context information for AI"""
        info_parts = []

        if intent:
            info_parts.append(f"🎯 Detected intent: {intent}")

        if products:
            info_parts.append(f"📦 Products found: {len(products)}")
            if len(products) <= 3:
                for p in products[:3]:
                    info_parts.append(f"  - {p.get('name', '')[:50]} @ Rs. {p.get('price', 0)}")

        if context:
            if context.get('selected_product'):
                p = context['selected_product']
                info_parts.append(f"🛒 Selected: {p.get('name', '')} - Rs. {p.get('price', 0)}")

            if context.get('quantity'):
                info_parts.append(f"🔢 Quantity: {context['quantity']}")

            if context.get('customer_name'):
                info_parts.append(f"👤 Customer: {context['customer_name']}")

            if context.get('contact_number'):
                info_parts.append(f"📱 Phone: {context['contact_number']}")

            if context.get('selected_district'):
                info_parts.append(f"📍 Location: {context.get('selected_location', '')}, {context['selected_district']}")

            if context.get('delivery_charge'):
                info_parts.append(f"🚚 Delivery: Rs. {context['delivery_charge']}")

        return "\n".join(info_parts) if info_parts else ""

    def _clean_response(self, response: str) -> str:
        """Remove thinking tags and clean up response"""
        # Remove <thinking>...</thinking> blocks
        response = re.sub(r'<thinking>[\s\S]*?</thinking>', '', response)
        # Remove any leftover tags
        response = re.sub(r'<[^>]+>', '', response)
        # Clean up extra whitespace
        response = re.sub(r'\n{3,}', '\n\n', response)
        return response.strip()

    def interpret_user_response(self, message: str, expected_type: str = "confirmation") -> Dict:
        """
        Use AI to interpret user response, handling typos and variations.

        Args:
            message: User's raw message
            expected_type: What we expect - "confirmation", "rejection", "phone", "order_id", "name", etc.

        Returns:
            Dict with interpreted meaning and confidence
        """
        if not self.is_available():
            return {"interpreted": message, "type": "unknown", "confidence": 0.5}

        try:
            prompt = f"""Interpret this user message in context. The bot is expecting a "{expected_type}" response.

User said: "{message}"

Determine:
1. What did they mean? (fix typos, understand intent)
2. Is this a: confirmation (yes), rejection (no), or something_else?
3. If it's data (phone, name, etc), extract it

Common typos to consider:
- "yss", "yees", "yess", "yas" = "yes"
- "noo", "npe", "nno" = "no"
- Numbers with spaces or dashes

Respond with JSON only:
{{"interpreted": "corrected message", "type": "confirmation/rejection/phone/order_id/name/other", "value": "extracted value if any", "confidence": 0.9}}"""

            response = self.client.chat.completions.create(
                model=self.model_fast,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.2
            )

            result_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{[\s\S]*?\}', result_text)
            if json_match:
                return json.loads(json_match.group())

            return {"interpreted": message, "type": "unknown", "confidence": 0.5}

        except Exception as e:
            print(f"Interpretation error: {e}")
            return {"interpreted": message, "type": "unknown", "confidence": 0.5}

    def is_confirmation_ai(self, message: str) -> bool:
        """Use AI to determine if message is a confirmation (yes)"""
        result = self.interpret_user_response(message, "confirmation")
        return result.get("type") == "confirmation" and result.get("confidence", 0) > 0.6

    def is_rejection_ai(self, message: str) -> bool:
        """Use AI to determine if message is a rejection (no)"""
        result = self.interpret_user_response(message, "rejection")
        return result.get("type") == "rejection" and result.get("confidence", 0) > 0.6

    def _fallback_response(self, intent: str, products: List[Dict] = None) -> str:
        """Generate fallback response when AI is unavailable"""
        fallbacks = {
            'greeting': "👋 Hello! Welcome to OVN Store. How can I help you today?",
            'product_search': f"🔍 Here are {len(products) if products else 'some'} products I found!",
            'flash_sale': "🔥 Check out our amazing flash sale deals!",
            'order_tracking': "📦 I can help you track your order. Please provide your order ID or phone number.",
            'order_placement': "🛒 I'd be happy to help you place an order!",
            'support': "🤝 I'm here to help with any issues. What's the problem?",
            'review_view': "⭐ Let me show you the reviews for this product.",
            'review_submit': "📝 I can help you submit a review. Which product would you like to review?",
            'policy': "📋 Free shipping on orders above Rs. 1000. 7-day return policy. Cash on Delivery available.",
            'thanks': "😊 You're welcome! Is there anything else I can help with?",
            'bye': "👋 Thank you for visiting OVN Store! Have a great day!",
            'general': "🤔 How can I help you today? You can browse products, track orders, or ask me anything!"
        }
        return fallbacks.get(intent, fallbacks['general'])
