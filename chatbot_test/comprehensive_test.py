"""
Comprehensive Test Suite for OVN Store Chatbot
Tests all scenarios including edge cases
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Set up path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot import OVNStoreChatbot

def test_scenario(bot, message, session_id, description):
    """Helper function to test a scenario and report results"""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")
    print(f"Input: {repr(message)}")

    try:
        result = bot.chat(message, session_id)
        print(f"SUCCESS - Got response")
        print(f"  Intent: {result.get('intent', 'N/A')}")
        print(f"  Message Preview: {result['message'][:200]}..." if len(result.get('message', '')) > 200 else f"  Message: {result.get('message', 'No message')}")
        if result.get('products'):
            print(f"  Products: {len(result['products'])} returned")
        if result.get('quick_replies'):
            print(f"  Quick Replies: {result['quick_replies']}")
        return {'success': True, 'result': result}
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e), 'type': type(e).__name__}


def run_all_tests():
    """Run all chatbot tests"""
    print("\n" + "="*80)
    print("OVN STORE CHATBOT - COMPREHENSIVE TEST SUITE")
    print("="*80)

    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }

    # Initialize chatbot
    print("\nInitializing chatbot...")
    try:
        bot = OVNStoreChatbot()
        print("Chatbot initialized successfully!")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize chatbot: {e}")
        import traceback
        traceback.print_exc()
        return results

    # ==================================================================
    # 1. GREETINGS
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 1: GREETINGS")
    print("#"*80)

    greetings = [
        ("hello", "greeting_1", "Basic hello"),
        ("hi", "greeting_2", "Short hi"),
        ("hey", "greeting_3", "Casual hey"),
        ("namaste", "greeting_4", "Nepali namaste"),
        ("good morning", "greeting_5", "Good morning"),
        ("good afternoon", "greeting_6", "Good afternoon"),
        ("good evening", "greeting_7", "Good evening"),
        ("howdy", "greeting_8", "Casual howdy"),
        ("greetings", "greeting_9", "Formal greetings"),
        ("Hello!", "greeting_10", "Hello with exclamation"),
        ("HELLO", "greeting_11", "Uppercase HELLO"),
        ("hELLo", "greeting_12", "Mixed case hello"),
    ]

    for msg, session, desc in greetings:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Greeting - {desc}: {res.get('error')}")

    # ==================================================================
    # 2. ORDER TRACKING
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 2: ORDER TRACKING")
    print("#"*80)

    # Basic tracking requests
    tracking_tests = [
        ("track my order", "track_1", "Basic track my order"),
        ("where is my order", "track_2", "Where is my order"),
        ("check my order", "track_3", "Check my order"),
        ("order status", "track_4", "Order status"),
        ("find my order", "track_5", "Find my order"),
        ("my order", "track_6", "Simple my order"),
        ("delivery status", "track_7", "Delivery status"),
    ]

    for msg, session, desc in tracking_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Order Tracking - {desc}: {res.get('error')}")

    # Tracking with typos
    typo_tests = [
        ("check my orde", "typo_1", "Typo: check my orde"),
        ("trck order", "typo_2", "Typo: trck order"),
        ("track my ordr", "typo_3", "Typo: track my ordr"),
        ("wher is my order", "typo_4", "Typo: wher is my order"),
        ("orderstatus", "typo_5", "No space: orderstatus"),
        ("track  my   order", "typo_6", "Extra spaces"),
    ]

    for msg, session, desc in typo_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Typo Test - {desc}: {res.get('error')}")

    # Phone number as input (should trigger order tracking)
    phone_tests = [
        ("9824236055", "phone_1", "Just phone number"),
        ("9841234567", "phone_2", "Another phone number"),
        ("my number is 9851234567", "phone_3", "Phone in sentence"),
        ("98-2423-6055", "phone_4", "Phone with dashes"),
    ]

    for msg, session, desc in phone_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Phone Test - {desc}: {res.get('error')}")

    # Order ID tests
    order_id_tests = [
        ("track order ABC12345", "orderid_1", "Order ID in message"),
        ("my order is abc12def", "orderid_2", "Lowercase order ID"),
    ]

    for msg, session, desc in order_id_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Order ID Test - {desc}: {res.get('error')}")

    # ==================================================================
    # 3. PRODUCT SEARCH
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 3: PRODUCT SEARCH")
    print("#"*80)

    product_tests = [
        ("show products", "prod_1", "Show products"),
        ("show me all products", "prod_2", "Show all products"),
        ("find bags", "prod_3", "Find specific: bags"),
        ("show me bags", "prod_4", "Show me specific category"),
        ("I'm looking for shoes", "prod_5", "Looking for specific"),
        ("do you have electronics", "prod_6", "Do you have category"),
        ("what products do you have", "prod_7", "What products"),
        ("browse products", "prod_8", "Browse products"),
        ("search for phone case", "prod_9", "Search for specific"),
        ("show categories", "categories_1", "Categories request"),
        ("what categories do you have", "categories_2", "Categories question"),
    ]

    for msg, session, desc in product_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Product Search - {desc}: {res.get('error')}")

    # Flash sale tests
    flash_tests = [
        ("show flash sales", "flash_1", "Flash sales"),
        ("deals", "flash_2", "Deals"),
        ("special offers", "flash_3", "Special offers"),
        ("discounted products", "flash_4", "Discounted products"),
        ("what's on sale", "flash_5", "What's on sale"),
    ]

    for msg, session, desc in flash_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Flash Sale - {desc}: {res.get('error')}")

    # Price queries
    price_tests = [
        ("products under 500", "price_1", "Products under price"),
        ("show me items below Rs. 1000", "price_2", "Items below price"),
        ("cheap products", "price_3", "Cheap products"),
    ]

    for msg, session, desc in price_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Price Query - {desc}: {res.get('error')}")

    # ==================================================================
    # 4. ORDER PLACEMENT
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 4: ORDER PLACEMENT")
    print("#"*80)

    order_placement_tests = [
        ("I want to buy", "buy_1", "I want to buy"),
        ("buy now", "buy_2", "Buy now"),
        ("purchase", "buy_3", "Purchase"),
        ("place order", "buy_4", "Place order"),
        ("I want to order", "buy_5", "I want to order"),
        ("I'll take it", "buy_6", "I'll take it"),
        ("add to cart", "buy_7", "Add to cart"),
    ]

    for msg, session, desc in order_placement_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Order Placement - {desc}: {res.get('error')}")

    # ==================================================================
    # 5. SUPPORT
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 5: SUPPORT")
    print("#"*80)

    support_tests = [
        ("I have a complaint", "support_1", "Complaint"),
        ("return my order", "support_2", "Return request"),
        ("I want a refund", "support_3", "Refund request"),
        ("help me", "support_4", "Help me"),
        ("speak to human", "support_5", "Speak to human"),
        ("my item is damaged", "support_6", "Damaged item"),
        ("wrong item delivered", "support_7", "Wrong item"),
        ("not working", "support_8", "Not working"),
        ("contact support", "support_9", "Contact support"),
    ]

    for msg, session, desc in support_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Support - {desc}: {res.get('error')}")

    # ==================================================================
    # 6. REVIEWS
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 6: REVIEWS")
    print("#"*80)

    review_tests = [
        ("show reviews for product", "review_1", "Show reviews"),
        ("reviews for vacuum cup", "review_2", "Reviews for specific"),
        ("what do people say about bags", "review_3", "What do people say"),
        ("customer reviews", "review_4", "Customer reviews"),
        ("write a review", "review_5", "Write review"),
        ("I want to review a product", "review_6", "Want to review"),
        ("rate product", "review_7", "Rate product"),
        ("give feedback", "review_8", "Give feedback"),
    ]

    for msg, session, desc in review_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Reviews - {desc}: {res.get('error')}")

    # ==================================================================
    # 7. POLICIES
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 7: POLICIES")
    print("#"*80)

    policy_tests = [
        ("shipping policy", "policy_1", "Shipping policy"),
        ("return policy", "policy_2", "Return policy"),
        ("refund policy", "policy_3", "Refund policy"),
        ("payment methods", "policy_4", "Payment methods"),
        ("how long does delivery take", "policy_5", "Delivery time"),
        ("do you have cash on delivery", "policy_6", "COD question"),
        ("cod available?", "policy_7", "COD abbreviation"),
    ]

    for msg, session, desc in policy_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Policies - {desc}: {res.get('error')}")

    # ==================================================================
    # 8. EDGE CASES
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 8: EDGE CASES")
    print("#"*80)

    edge_case_tests = [
        ("", "edge_1", "Empty message"),
        ("   ", "edge_2", "Whitespace only"),
        ("a", "edge_3", "Single character"),
        ("??", "edge_4", "Special characters only"),
        ("12345", "edge_5", "Numbers only (not phone)"),
        ("@#$%^&*", "edge_6", "Symbols only"),
        ("a" * 500, "edge_7", "Very long message (500 chars)"),
        ("hello " * 100, "edge_8", "Repeated words (long)"),
        ("What is the meaning of life?", "edge_9", "Unrelated question"),
        ("asdfghjkl", "edge_10", "Random letters"),
        ("!!!!!!!", "edge_11", "Multiple exclamations"),
        ("...", "edge_12", "Ellipsis"),
        ("  hello  ", "edge_13", "Message with leading/trailing spaces"),
        ("TRACK MY ORDER!!!", "edge_14", "All caps with punctuation"),
    ]

    for msg, session, desc in edge_case_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Edge Case - {desc}: {res.get('error')}")

    # Nepali/Roman Nepali tests
    nepali_tests = [
        ("kati price", "nepali_1", "Roman Nepali: kati price"),
        ("yo kinna", "nepali_2", "Roman Nepali: yo kinna"),
        ("mero order", "nepali_3", "Roman Nepali: mero order"),
        ("order kaha", "nepali_4", "Roman Nepali: order kaha"),
    ]

    for msg, session, desc in nepali_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Nepali - {desc}: {res.get('error')}")

    # ==================================================================
    # 9. CONFIRMATION/REJECTION
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 9: CONFIRMATION/REJECTION")
    print("#"*80)

    # First start an order tracking flow, then test confirmations
    print("\n--- Testing confirmation in order tracking flow ---")

    # Start tracking flow
    res = test_scenario(bot, "track my order", "confirm_flow_1", "Start tracking flow")
    if res['success']:
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(f"Confirm Flow - Start: {res.get('error')}")

    # Test various confirmations
    confirm_tests = [
        ("yes", "confirm_1", "Simple yes"),
        ("y", "confirm_2", "Single letter y"),
        ("yeah", "confirm_3", "Yeah"),
        ("yep", "confirm_4", "Yep"),
        ("yup", "confirm_5", "Yup"),
        ("ok", "confirm_6", "Ok"),
        ("okay", "confirm_7", "Okay"),
        ("sure", "confirm_8", "Sure"),
        ("Yes", "confirm_9", "Capitalized Yes"),
        ("YES", "confirm_10", "All caps YES"),
    ]

    for msg, session, desc in confirm_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Confirmation - {desc}: {res.get('error')}")

    # Test rejections
    reject_tests = [
        ("no", "reject_1", "Simple no"),
        ("n", "reject_2", "Single letter n"),
        ("nope", "reject_3", "Nope"),
        ("nah", "reject_4", "Nah"),
        ("cancel", "reject_5", "Cancel"),
        ("No", "reject_6", "Capitalized No"),
        ("NO", "reject_7", "All caps NO"),
    ]

    for msg, session, desc in reject_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Rejection - {desc}: {res.get('error')}")

    # ==================================================================
    # 10. STATE TRANSITIONS
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 10: STATE TRANSITIONS")
    print("#"*80)

    # Test flow: Start tracking, then switch to product search
    print("\n--- Testing state transition: Order tracking -> Product search ---")
    session_id = "state_transition_1"

    res = test_scenario(bot, "track my order", session_id, "Start order tracking")
    if res['success']:
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(f"State Transition - Start tracking: {res.get('error')}")

    # Now cancel and search products
    res = test_scenario(bot, "cancel", session_id, "Cancel tracking")
    if res['success']:
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(f"State Transition - Cancel: {res.get('error')}")

    res = test_scenario(bot, "show products", session_id, "Switch to product search")
    if res['success']:
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(f"State Transition - Product search: {res.get('error')}")

    # Test flow: Start buy, then cancel
    print("\n--- Testing state transition: Order placement -> Cancel ---")
    session_id = "state_transition_2"

    res = test_scenario(bot, "I want to buy", session_id, "Start buy flow")
    if res['success']:
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(f"State Transition - Start buy: {res.get('error')}")

    res = test_scenario(bot, "nevermind", session_id, "Cancel mid-flow with nevermind")
    if res['success']:
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(f"State Transition - Nevermind: {res.get('error')}")

    # Test flow: Support -> Cancel -> New flow
    print("\n--- Testing state transition: Support -> Cancel -> Greeting ---")
    session_id = "state_transition_3"

    res = test_scenario(bot, "I have a complaint", session_id, "Start support")
    if res['success']:
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(f"State Transition - Start support: {res.get('error')}")

    res = test_scenario(bot, "go back", session_id, "Cancel with go back")
    if res['success']:
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(f"State Transition - Go back: {res.get('error')}")

    res = test_scenario(bot, "hello", session_id, "New greeting after cancel")
    if res['success']:
        results['passed'] += 1
    else:
        results['failed'] += 1
        results['errors'].append(f"State Transition - New greeting: {res.get('error')}")

    # ==================================================================
    # 11. THANKS AND BYE
    # ==================================================================
    print("\n" + "#"*80)
    print("# SECTION 11: THANKS AND BYE")
    print("#"*80)

    thanks_bye_tests = [
        ("thank you", "thanks_1", "Thank you"),
        ("thanks", "thanks_2", "Thanks"),
        ("thank you so much", "thanks_3", "Thank you so much"),
        ("bye", "bye_1", "Bye"),
        ("goodbye", "bye_2", "Goodbye"),
        ("see you later", "bye_3", "See you later"),
        ("exit", "bye_4", "Exit"),
    ]

    for msg, session, desc in thanks_bye_tests:
        res = test_scenario(bot, msg, session, desc)
        if res['success']:
            results['passed'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(f"Thanks/Bye - {desc}: {res.get('error')}")

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")

    if results['errors']:
        print(f"\nFailed Tests ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"  - {error}")
    else:
        print("\nAll tests passed!")

    return results


if __name__ == "__main__":
    run_all_tests()
