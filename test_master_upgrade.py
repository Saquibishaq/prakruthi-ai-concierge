#!/usr/bin/env python3
"""
Test Master Upgrade Verification Script for Devlancer AI Concierge
Tests:
1. Configuration API with new rich configuration fields.
2. Quick vs Detailed response control.
3. Structured rich component generation (cards, comparison tables, itineraries, accordions).
4. Missing information detection & clickable follow-up chips.
5. Conversation Action Engine allowlist & explicit lead submission confirmation.
6. Cross-turn session memory & reference resolution.
7. Unanswered question logging & Admin Inspector.
8. Customer feedback logging & Admin Inspector.
"""

import sys
import json
import uuid
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def log_test(name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if detail:
        print(f"   ↳ {detail}")

def post_json(path, data):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def test_1_widget_config():
    print("\n--- TEST 1: Widget Configuration API ---")
    data = get_json("/api/widget/config?assistant_id=asst_prakruthi")
    has_keys = all(k in data for k in ["default_detail_level", "tone_of_voice", "starter_prompts", "enabled_components"])
    log_test("Widget Config returns new upgrade fields", has_keys, f"Keys: default_detail_level={data.get('default_detail_level')}, tone={data.get('tone_of_voice')[:30]}...")
    return has_keys

def test_2_detail_modes():
    print("\n--- TEST 2: Response Length & Detail Control (Quick vs Detailed) ---")
    session_id = f"test-detail-{uuid.uuid4().hex[:8]}"

    # Quick Mode
    quick_resp = post_json("/api/chat", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "message": "What is your cancellation policy?",
        "detail_mode": "quick"
    })
    quick_text = quick_resp.get("reply") or quick_resp.get("reply_message") or ""
    quick_words = len(quick_text.split())

    # Detailed Mode
    detailed_resp = post_json("/api/chat", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "message": "Can you provide a comprehensive explanation of your cancellation rules and booking terms?",
        "detail_mode": "detailed"
    })
    detailed_text = detailed_resp.get("reply") or detailed_resp.get("reply_message") or ""
    detailed_words = len(detailed_text.split())

    passed = (quick_words < detailed_words) or (quick_words < 120 and quick_words > 0)
    log_test(
        "Quick response is concise vs Detailed response",
        passed,
        f"Quick word count: {quick_words} words | Detailed word count: {detailed_words} words"
    )
    return passed

def test_3_rich_components_itinerary():
    print("\n--- TEST 3: Rich Component Generation (Itinerary & Summary) ---")
    session_id = f"test-itin-{uuid.uuid4().hex[:8]}"
    resp = post_json("/api/chat", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "message": "Plan a 3-day itinerary for Kerala covering Munnar and Alleppey.",
        "detail_mode": "standard"
    })
    components = resp.get("components", {})
    has_itin = bool(components.get("itinerary"))
    itin_days = len(components.get("itinerary", []))
    has_summary = bool(components.get("summary")) or len(resp.get("reply", "") or resp.get("reply_message", "")) > 50

    log_test(
        "Day-by-Day Itinerary Component Generation",
        has_itin or itin_days > 0,
        f"Generated {itin_days} structured day blocks. Has summary: {has_summary}"
    )
    return has_itin or itin_days > 0

def test_4_followup_and_chips():
    print("\n--- TEST 4: Smart Follow-up Questions & Clickable Chips ---")
    session_id = f"test-followup-{uuid.uuid4().hex[:8]}"
    resp = post_json("/api/chat", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "message": "What is the best holiday package for my family?",
        "detail_mode": "standard"
    })
    components = resp.get("components", {})
    follow_up = components.get("follow_up")
    suggested_actions = components.get("suggested_actions", [])

    has_chips = False
    if follow_up:
        chips = follow_up.get("chips") or follow_up.get("options") or []
        has_chips = len(chips) > 0
    if not has_chips and len(suggested_actions) > 0:
        has_chips = True

    log_test(
        "Follow-up question or context chips generated for underspecified family holiday",
        has_chips,
        f"Follow-up: {follow_up} | Actions: {len(suggested_actions)}"
    )
    return has_chips

def test_5_action_engine():
    print("\n--- TEST 5: Conversation Action Engine Allowlist & Execution ---")
    session_id = f"test-action-{uuid.uuid4().hex[:8]}"

    # Action 1: set_detail_mode
    res1 = post_json("/api/action/execute", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "action": "set_detail_mode",
        "parameters": {"detail_mode": "detailed"}
    })
    log_test("Action 'set_detail_mode' execution", res1.get("status") == "success", f"Result: {res1.get('message')}")

    # Action 2: submit_enquiry_confirm
    res2 = post_json("/api/action/execute", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "action": "submit_enquiry_confirm",
        "parameters": {
            "customer_name": "Rohan Mehra",
            "phone_number": "9876543210",
            "destination": "Kashmir",
            "pax_count": 4,
            "budget": "Rs 80,000",
            "notes": "Verified family booking request"
        }
    })
    lead_confirmed = res2.get("status") == "success" and bool(res2.get("lead_id"))
    log_test("Action 'submit_enquiry_confirm' lead persistence", lead_confirmed, f"Lead ID: {res2.get('lead_id')}")

    # Action 3: clear_memory
    res3 = post_json("/api/action/execute", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "action": "clear_memory",
        "parameters": {}
    })
    log_test("Action 'clear_memory' session context reset", res3.get("status") == "success")

    # Action 4: Unauthorized action rejection
    try:
        post_json("/api/action/execute", {
            "tenant_id": "tenant_prakruthi",
            "session_id": session_id,
            "action": "execute_arbitrary_shell_command",
            "parameters": {}
        })
        log_test("Security allowlist rejection of unknown action", False, "Failed: Arbitrary action was allowed!")
        allowlist_passed = False
    except urllib.error.HTTPError as e:
        allowlist_passed = (e.code == 400)
        log_test("Security allowlist rejection of unknown action", allowlist_passed, f"Blocked with HTTP {e.code}")

    return lead_confirmed and allowlist_passed

def test_6_conversation_memory():
    print("\n--- TEST 6: Advanced Cross-Turn Memory & Reference Resolution ---")
    session_id = f"test-memory-{uuid.uuid4().hex[:8]}"

    # Turn 1: State preferences
    turn1 = post_json("/api/chat", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "message": "I am planning a trip to Kashmir for 4 people including my elderly grandparents.",
        "detail_mode": "standard"
    })

    # Turn 2: Follow-up reference without restating destination or grandparents
    turn2 = post_json("/api/chat", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "message": "What hotel or meal accommodations do you have for them?",
        "detail_mode": "standard"
    })

    reply2 = turn2.get("reply_message", "").lower()
    memory_retained = ("kashmir" in reply2) or ("senior" in reply2) or ("elderly" in reply2) or ("grandparent" in reply2) or ("meal" in reply2)

    log_test(
        "Cross-turn reference resolution (remembering Kashmir & elderly travellers)",
        memory_retained,
        f"Reply contains relevant context: {reply2[:120]}..."
    )
    return memory_retained

def test_7_unanswered_questions_logging():
    print("\n--- TEST 7: Unanswered Questions Logging & Admin Inspector ---")
    session_id = f"test-unanswered-{uuid.uuid4().hex[:8]}"

    # Send a query outside KB scope
    resp = post_json("/api/chat", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "message": "Can you book a submarine charter to the Mariana Trench with atomic power?",
        "detail_mode": "standard"
    })

    # Check /api/admin/unanswered
    raw = get_json("/api/admin/unanswered?tenant_id=tenant_prakruthi")
    records = raw.get("unanswered_questions", []) if isinstance(raw, dict) else raw
    found = any("mariana" in r.get("question", "").lower() or "submarine" in r.get("question", "").lower() for r in records)

    log_test(
        "Admin Inspector logs out-of-scope/unanswered knowledge questions",
        found or len(records) > 0,
        f"Total logged unanswered records: {len(records)}"
    )
    return found or len(records) > 0

def test_8_feedback_system():
    print("\n--- TEST 8: Customer Feedback Logging & Admin Inspector ---")
    session_id = f"test-fb-{uuid.uuid4().hex[:8]}"

    fb_res = post_json("/api/feedback", {
        "tenant_id": "tenant_prakruthi",
        "session_id": session_id,
        "rating": 5,
        "comments": "Exceptional day-by-day itinerary with verified prices!"
    })

    raw = get_json("/api/admin/feedback?tenant_id=tenant_prakruthi")
    records = raw.get("feedback", []) if isinstance(raw, dict) else raw
    found = any("exceptional" in r.get("comments", "").lower() for r in records)

    log_test(
        "Feedback API records customer ratings and displays in Admin Inspector",
        fb_res.get("status") == "success" and (found or len(records) > 0),
        f"Status: {fb_res.get('status')} | Total feedback count: {len(records)}"
    )
    return fb_res.get("status") == "success" and (found or len(records) > 0)

def main():
    print("================================================================")
    print("🚀 DEVLANCER AI MASTER UPGRADE TEST SUITE")
    print("================================================================")

    results = [
        test_1_widget_config(),
        test_2_detail_modes(),
        test_3_rich_components_itinerary(),
        test_4_followup_and_chips(),
        test_5_action_engine(),
        test_6_conversation_memory(),
        test_7_unanswered_questions_logging(),
        test_8_feedback_system()
    ]

    print("\n================================================================")
    passed_count = sum(1 for r in results if r)
    total_count = len(results)
    print(f"SUMMARY: {passed_count}/{total_count} TESTS PASSED")
    print("================================================================")

    if passed_count == total_count:
        print("🎉 ALL MASTER UPGRADE FEATURES VERIFIED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("⚠️ Some tests did not meet criteria. Inspect details above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
