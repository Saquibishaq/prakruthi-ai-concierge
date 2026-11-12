import httpx
import json

base = "http://127.0.0.1:8000"

print("--- 1. Testing GET /api/tenants ---")
r = httpx.get(f"{base}/api/tenants")
print("Status:", r.status_code)
tenants = r.json()
print(f"Total Tenants: {len(tenants)}")
for t in tenants:
    name = t.get("name")
    slug = t.get("slug")
    asst_id = t.get("assistant_id")
    verified = t.get("installation_verified")
    print(f" - {name} (Slug: {slug}, Asst ID: {asst_id}, Verified: {verified})")

print("\n--- 2. Testing GET /api/widget/config (Many2Go) ---")
r = httpx.get(f"{base}/api/widget/config?assistant_id=asst_many2go_holidays")
print("Status:", r.status_code)
cfg = r.json()
print("Agency Name:", cfg.get("name"))
print("Primary Color:", cfg.get("primary_color"))
print("Packages Count:", len(cfg.get("packages", [])))

print("\n--- 3. Testing POST /api/chat (Many2Go) ---")
chat_payload = {
    "assistant_id": "asst_many2go_holidays",
    "session_id": "test_verification_session_1",
    "message": "Hi, what are your top fixed departures for Europe?"
}
r = httpx.post(f"{base}/api/chat", json=chat_payload, timeout=50.0)
print("Status:", r.status_code)
chat_res = r.json()
print("AI Reply (preview):", chat_res["reply"][:150], "...")
print("Quick Replies:", chat_res.get("quick_replies"))
print("Lead State:", chat_res.get("lead_state"))

print("\n--- 4. Testing Lead Extraction with Phone Number ---")
lead_payload = {
    "assistant_id": "asst_many2go_holidays",
    "session_id": "test_verification_session_1",
    "message": "My name is Rajesh, phone +91 9876543210. We are 2 adults planning for Switzerland in May."
}
r = httpx.post(f"{base}/api/chat", json=lead_payload, timeout=50.0)
print("Status:", r.status_code)
lead_res = r.json()
print("CRM Synced Now:", lead_res.get("crm_synced_now"))
print("Extracted Lead:", lead_res.get("lead_state"))

print("\n--- 5. Testing GET /api/leads ---")
r = httpx.get(f"{base}/api/leads")
leads = r.json().get("leads", [])
print(f"Total Leads in CRM: {len(leads)}")
latest = leads[0] if leads else None
if latest:
    print("Latest Lead:", latest.get("customer_name"), latest.get("phone_number"), latest.get("destination"), latest.get("lead_score"))

print("\n--- 6. Testing /api/verify-install Crawler ---")
r = httpx.post(f"{base}/api/verify-install", json={"slug": "many2go-holidays"}, timeout=15.0)
print("Verify Install Result:", r.json())

print("\n--- 7. Testing /api/feedback ---")
r = httpx.post(f"{base}/api/feedback", json={
    "assistant_id": "asst_many2go_holidays",
    "session_id": "test_verification_session_1",
    "rating": "up",
    "comment": "Quick and helpful"
})
print("Feedback Result:", r.json())

print("\n--- 8. Testing /api/analytics ---")
r = httpx.get(f"{base}/api/analytics")
print("Analytics:", r.json())
