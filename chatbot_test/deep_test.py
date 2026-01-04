"""
Deep Testing for OVN Store Chatbot
Tests complete flows, edge cases, and potential breaking scenarios
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot import OVNStoreChatbot

def test_with_details(bot, message, session_id, description):
    """Test a scenario and return detailed results"""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"Input: {repr(message)}")

    try:
        result = bot.chat(message, session_id)
        print(f"  Intent: {result.get('intent', 'N/A')}")
        msg = result.get('message', '')
        print(f"  Response: {msg[:150]}..." if len(msg) > 150 else f"  Response: {msg}")
        return {'success': True, 'result': result, 'intent': result.get('intent')}
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}


def test_complete_order_flow():
    """Test complete order placement flow from start to finish"""
    print("\n" + "#"*80)
    print("# COMPLETE ORDER PLACEMENT FLOW TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    session_id = "complete_order_flow"
    errors = []

    steps = [
        ("I want to buy a vacuum cup", "Step 1: Start buy with product name"),
        ("yes", "Step 2: Confirm product"),
        ("2", "Step 3: Choose to buy (option 2)"),
        ("2", "Step 4: Enter quantity"),
        ("John Doe", "Step 5: Enter name"),
        ("9841234567", "Step 6: Enter phone"),
        ("Kathmandu", "Step 7: Select district"),
        ("Kathmandu - Inside Ringroad", "Step 8: Select location"),
        ("Near Airport", "Step 9: Enter landmark"),
        ("no", "Step 10: Cancel order (don't actually place it)")
    ]

    for msg, desc in steps:
        res = test_with_details(bot, msg, session_id, desc)
        if not res['success']:
            errors.append(f"{desc}: {res.get('error')}")

    return errors


def test_complete_support_flow():
    """Test complete support flow from start to finish"""
    print("\n" + "#"*80)
    print("# COMPLETE SUPPORT FLOW TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    session_id = "complete_support_flow"
    errors = []

    steps = [
        ("I have a problem", "Step 1: Start support"),
        ("My order is late and I'm worried", "Step 2: Enter complaint details"),
        ("test@example.com", "Step 3: Enter email"),
        ("cancel", "Step 4: Cancel support request")
    ]

    for msg, desc in steps:
        res = test_with_details(bot, msg, session_id, desc)
        if not res['success']:
            errors.append(f"{desc}: {res.get('error')}")

    return errors


def test_complete_review_flow():
    """Test complete review flow"""
    print("\n" + "#"*80)
    print("# COMPLETE REVIEW FLOW TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    session_id = "complete_review_flow"
    errors = []

    steps = [
        ("write a review for vacuum cup", "Step 1: Start review"),
        ("1", "Step 2: Select first product if needed"),
    ]

    for msg, desc in steps:
        res = test_with_details(bot, msg, session_id, desc)
        if not res['success']:
            errors.append(f"{desc}: {res.get('error')}")

    return errors


def test_session_state_persistence():
    """Test that session state persists correctly"""
    print("\n" + "#"*80)
    print("# SESSION STATE PERSISTENCE TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    session_id = "state_persistence"
    errors = []

    # Start a flow
    res1 = test_with_details(bot, "track my order", session_id, "Start tracking flow")
    if not res1['success']:
        errors.append(f"Start flow: {res1.get('error')}")
        return errors

    # Get session info
    session_info = bot.get_session_info(session_id)
    print(f"\nSession state after start: {session_info.get('state', 'N/A')}")

    # Check state is not IDLE
    if session_info.get('state') == 'idle':
        errors.append("State should not be IDLE after starting tracking flow")

    # Continue with phone
    res2 = test_with_details(bot, "9824236055", session_id, "Provide phone number")
    if not res2['success']:
        errors.append(f"Provide phone: {res2.get('error')}")

    # Session should now be back to IDLE after showing order
    session_info = bot.get_session_info(session_id)
    print(f"\nSession state after order details: {session_info.get('state', 'N/A')}")

    return errors


def test_unicode_and_special_characters():
    """Test handling of unicode and special characters"""
    print("\n" + "#"*80)
    print("# UNICODE AND SPECIAL CHARACTERS TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    errors = []

    test_cases = [
        # Unicode tests
        ("", "unicode_1", "Nepali text"),
        ("", "unicode_2", "Chinese text"),
        ("Emoji test: ", "unicode_3", "Emoji in message"),
        ("", "unicode_4", "Arabic text"),
        ("Cafe", "unicode_5", "Accent character"),
        # Special formatting
        ("**bold** text", "format_1", "Markdown bold"),
        ("<script>alert('xss')</script>", "xss_1", "XSS attempt"),
        ("SELECT * FROM users", "sql_1", "SQL injection attempt"),
        ("'; DROP TABLE orders; --", "sql_2", "SQL injection 2"),
        # Control characters
        ("hello\x00world", "ctrl_1", "Null character"),
        ("hello\nworld", "ctrl_2", "Newline character"),
        ("hello\tworld", "ctrl_3", "Tab character"),
        ("hello\rworld", "ctrl_4", "Carriage return"),
    ]

    for msg, session, desc in test_cases:
        res = test_with_details(bot, msg, session, desc)
        if not res['success']:
            errors.append(f"{desc}: {res.get('error')}")

    return errors


def test_rapid_state_changes():
    """Test rapid switching between different flows"""
    print("\n" + "#"*80)
    print("# RAPID STATE CHANGES TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    session_id = "rapid_changes"
    errors = []

    # Rapidly switch between different intents
    rapid_tests = [
        ("track my order", "Track order"),
        ("cancel", "Cancel"),
        ("buy vacuum cup", "Buy product"),
        ("cancel", "Cancel"),
        ("I have a complaint", "Start support"),
        ("cancel", "Cancel"),
        ("write a review", "Start review"),
        ("cancel", "Cancel"),
        ("hello", "Back to greeting"),
    ]

    for msg, desc in rapid_tests:
        res = test_with_details(bot, msg, session_id, desc)
        if not res['success']:
            errors.append(f"{desc}: {res.get('error')}")

    return errors


def test_extreme_inputs():
    """Test extreme input scenarios"""
    print("\n" + "#"*80)
    print("# EXTREME INPUTS TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    errors = []

    extreme_tests = [
        # Length tests
        ("", "empty_1", "Empty string"),
        (" " * 100, "space_1", "100 spaces"),
        ("a" * 10000, "long_1", "10000 character message"),
        ("hello " * 1000, "long_2", "Repeated word (1000x)"),
        # Number tests
        ("0", "num_1", "Zero"),
        ("-1", "num_2", "Negative number"),
        ("9999999999999999999999", "num_3", "Very large number"),
        ("0.001", "num_4", "Small decimal"),
        # Boolean-like
        ("true", "bool_1", "True string"),
        ("false", "bool_2", "False string"),
        ("null", "bool_3", "Null string"),
        ("undefined", "bool_4", "Undefined string"),
        ("None", "bool_5", "None string"),
        # JSON-like
        ('{"key": "value"}', "json_1", "JSON string"),
        ('[1, 2, 3]', "json_2", "JSON array"),
        # Path-like
        ('C:\\Windows\\System32', "path_1", "Windows path"),
        ('/etc/passwd', "path_2", "Linux path"),
        ('../../../etc/passwd', "path_3", "Path traversal attempt"),
    ]

    for msg, session, desc in extreme_tests:
        res = test_with_details(bot, msg, session, desc)
        if not res['success']:
            errors.append(f"{desc}: {res.get('error')}")

    return errors


def test_concurrent_sessions():
    """Test multiple concurrent sessions"""
    print("\n" + "#"*80)
    print("# CONCURRENT SESSIONS TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    errors = []

    # Simulate multiple users
    sessions = {
        "user_1": ["hello", "track my order", "9824236055"],
        "user_2": ["show products", "buy vacuum cup", "yes"],
        "user_3": ["I have a complaint", "order is late", "test@test.com"],
    }

    for session_id, messages in sessions.items():
        for msg in messages:
            res = test_with_details(bot, msg, session_id, f"{session_id}: {msg[:30]}")
            if not res['success']:
                errors.append(f"{session_id} - {msg[:30]}: {res.get('error')}")

    # Check active sessions count
    count = bot.get_active_sessions()
    print(f"\nActive sessions: {count}")

    return errors


def test_confirmation_variations():
    """Test various forms of confirmation and rejection"""
    print("\n" + "#"*80)
    print("# CONFIRMATION VARIATIONS TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    errors = []

    # Test confirmations in context
    confirmation_tests = [
        # Start flow then test confirmation
        [("track my order", "Start flow"), ("yss", "Typo: yss")],
        [("track my order", "Start flow"), ("yea", "Yea")],
        [("track my order", "Start flow"), ("ye", "Ye")],
        [("track my order", "Start flow"), ("yah", "Yah")],
        [("track my order", "Start flow"), ("uh huh", "Uh huh")],
        [("track my order", "Start flow"), ("affirmative", "Affirmative")],
        [("track my order", "Start flow"), ("go ahead", "Go ahead")],
    ]

    for i, flow in enumerate(confirmation_tests):
        session_id = f"confirm_var_{i}"
        for msg, desc in flow:
            res = test_with_details(bot, msg, session_id, desc)
            if not res['success']:
                errors.append(f"{desc}: {res.get('error')}")

    return errors


def test_intent_detection_edge_cases():
    """Test intent detection edge cases"""
    print("\n" + "#"*80)
    print("# INTENT DETECTION EDGE CASES TEST")
    print("#"*80)

    bot = OVNStoreChatbot()
    errors = []

    # Ambiguous intents
    ambiguous_tests = [
        ("I want to track and buy", "ambig_1", "Track and buy together"),
        ("show me order products", "ambig_2", "Order with products"),
        ("return to products", "ambig_3", "Return with products"),
        ("review my order", "ambig_4", "Review with order"),
        ("help me buy", "ambig_5", "Help with buy"),
        ("complaint about product", "ambig_6", "Complaint about product"),
        ("track product delivery", "ambig_7", "Track with product and delivery"),
    ]

    for msg, session, desc in ambiguous_tests:
        res = test_with_details(bot, msg, session, desc)
        if not res['success']:
            errors.append(f"{desc}: {res.get('error')}")
        else:
            print(f"  Detected intent: {res.get('intent')}")

    return errors


def run_all_deep_tests():
    """Run all deep tests"""
    print("\n" + "="*80)
    print("OVN STORE CHATBOT - DEEP TEST SUITE")
    print("="*80)

    all_errors = []

    # Run each test suite
    test_suites = [
        ("Complete Order Flow", test_complete_order_flow),
        ("Complete Support Flow", test_complete_support_flow),
        ("Complete Review Flow", test_complete_review_flow),
        ("Session State Persistence", test_session_state_persistence),
        ("Unicode and Special Characters", test_unicode_and_special_characters),
        ("Rapid State Changes", test_rapid_state_changes),
        ("Extreme Inputs", test_extreme_inputs),
        ("Concurrent Sessions", test_concurrent_sessions),
        ("Confirmation Variations", test_confirmation_variations),
        ("Intent Detection Edge Cases", test_intent_detection_edge_cases),
    ]

    for suite_name, suite_func in test_suites:
        try:
            errors = suite_func()
            if errors:
                all_errors.extend([f"[{suite_name}] {e}" for e in errors])
        except Exception as e:
            import traceback
            all_errors.append(f"[{suite_name}] SUITE ERROR: {type(e).__name__}: {e}")
            print(f"\nSUITE ERROR in {suite_name}:")
            traceback.print_exc()

    # Summary
    print("\n" + "="*80)
    print("DEEP TEST SUMMARY")
    print("="*80)

    if all_errors:
        print(f"ERRORS FOUND: {len(all_errors)}")
        for error in all_errors:
            print(f"  - {error}")
    else:
        print("ALL DEEP TESTS PASSED!")

    return all_errors


if __name__ == "__main__":
    run_all_deep_tests()
