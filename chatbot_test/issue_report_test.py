"""
Issue Report Test - Identifies specific issues found during testing
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot import OVNStoreChatbot

def test_issue(bot, messages, session_id, description, expected_behavior):
    """Test a potential issue with expected behavior"""
    print(f"\n{'='*70}")
    print(f"ISSUE: {description}")
    print(f"Expected: {expected_behavior}")
    print(f"{'='*70}")

    for i, msg in enumerate(messages, 1):
        print(f"\nStep {i}: Input: {repr(msg)}")
        try:
            result = bot.chat(msg, session_id)
            print(f"  Response: {result.get('message', '')[:150]}...")
            print(f"  Intent: {result.get('intent', 'N/A')}")
        except Exception as e:
            print(f"  ERROR: {e}")


def run_issue_tests():
    """Run specific issue tests"""
    print("\n" + "="*80)
    print("CHATBOT ISSUE IDENTIFICATION TESTS")
    print("="*80)

    bot = OVNStoreChatbot()

    # Issue 1: Product selection in order flow doesn't work with "yes"
    print("\n" + "#"*80)
    print("# ISSUE 1: Product confirmation with 'yes' in order flow")
    print("#"*80)
    test_issue(
        bot,
        ["I want to buy vacuum cup", "1", "yes"],
        "issue_1",
        "Selecting product by number, then confirming with 'yes'",
        "Should confirm the product and ask for next step, not search for 'yes'"
    )

    # Issue 2: Number selection interpreted as product search
    print("\n" + "#"*80)
    print("# ISSUE 2: Number selection in multi-product results")
    print("#"*80)
    bot2 = OVNStoreChatbot()
    test_issue(
        bot2,
        ["buy vacuum cup", "1"],
        "issue_2",
        "When multiple products shown, selecting '1' should pick first product",
        "Should select the first product, not search for '1'"
    )

    # Issue 3: "return my order" detected as order_tracking
    print("\n" + "#"*80)
    print("# ISSUE 3: 'return my order' detected as order_tracking instead of support")
    print("#"*80)
    bot3 = OVNStoreChatbot()
    test_issue(
        bot3,
        ["return my order"],
        "issue_3",
        "'return my order' should trigger support flow",
        "Should start return/refund support flow, not order tracking"
    )

    # Issue 4: "discounted products" triggers review_submit
    print("\n" + "#"*80)
    print("# ISSUE 4: 'discounted products' triggers review_submit")
    print("#"*80)
    bot4 = OVNStoreChatbot()
    test_issue(
        bot4,
        ["discounted products"],
        "issue_4",
        "'discounted products' should show flash sale products",
        "Should show discounted/flash sale products, not start review flow"
    )

    # Issue 5: "I want to order" triggers general instead of order_placement
    print("\n" + "#"*80)
    print("# ISSUE 5: 'I want to order' triggers general instead of order_placement")
    print("#"*80)
    bot5 = OVNStoreChatbot()
    test_issue(
        bot5,
        ["I want to order"],
        "issue_5",
        "'I want to order' should start order placement",
        "Should start order placement flow, not general response"
    )

    # Issue 6: "track product delivery" triggers review_submit
    print("\n" + "#"*80)
    print("# ISSUE 6: 'track product delivery' triggers review_submit")
    print("#"*80)
    bot6 = OVNStoreChatbot()
    test_issue(
        bot6,
        ["track product delivery"],
        "issue_6",
        "'track product delivery' should trigger order tracking",
        "Should start order tracking, not review submission"
    )

    # Issue 7: "show reviews for product" triggers product_search
    print("\n" + "#"*80)
    print("# ISSUE 7: 'show reviews for product' triggers product_search")
    print("#"*80)
    bot7 = OVNStoreChatbot()
    test_issue(
        bot7,
        ["show reviews for product"],
        "issue_7",
        "'show reviews for product' should show reviews",
        "Should trigger review_view intent, not product_search"
    )

    # Issue 8: Confirmation in order placement selecting product state
    print("\n" + "#"*80)
    print("# ISSUE 8: 'yes' not working in ORDER_PLACEMENT_CONFIRMING_PRODUCT state")
    print("#"*80)
    bot8 = OVNStoreChatbot()
    test_issue(
        bot8,
        ["buy vacuum cup", "1", "yes", "2", "1"],
        "issue_8",
        "After selecting product and it asks 'Is this the product you want?', 'yes' should confirm",
        "Should proceed to ask what action (details or buy), not search for 'yes'"
    )

    print("\n" + "="*80)
    print("ISSUES SUMMARY")
    print("="*80)
    print("""
IDENTIFIED ISSUES:

1. CONFIRMATION BUG: When in ORDER_PLACEMENT_CONFIRMING_PRODUCT state, saying
   'yes' doesn't confirm the product - instead it searches for 'yes' as a product.
   This is because the intent detection overrides the state-based routing.

2. NUMBER SELECTION BUG: When in ORDER_PLACEMENT_SELECTING_PRODUCT state,
   entering a number like '1' should select the product, but it may search
   for products matching '1' instead.

3. INTENT CONFLICT - 'return my order': The word 'order' triggers order_tracking
   intent when it should trigger support (return/refund).

4. INTENT CONFLICT - 'discounted products': The word 'products' with 'discounted'
   somehow triggers review_submit instead of flash_sale or product_search.

5. MISSING INTENT - 'I want to order': This should trigger order_placement but
   triggers general response.

6. INTENT CONFLICT - 'track product delivery': Multiple intent keywords present
   causing wrong intent (review_submit instead of order_tracking).

7. INTENT CONFLICT - 'show reviews for product': The word 'show' triggers
   product_search over review_view.

8. STATE HANDLING: When in an active state/flow, user confirmations and
   selections should be handled by the current handler, not re-detected as
   new intents.

ROOT CAUSE ANALYSIS:
The main issue appears to be that intent detection runs on every message,
even when the user is in an active flow/state. The state-based routing
should take precedence, but the intent detection is overriding it in some
cases.

In the _get_handler method of chatbot.py, it checks state first but then
also checks intent. The issue is that handlers check if they can_handle
the intent, but when in a flow, the handler should handle ANY message
from the user in that state, not just messages matching specific intents.
""")


if __name__ == "__main__":
    run_issue_tests()
