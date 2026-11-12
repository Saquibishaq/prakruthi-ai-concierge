#!/usr/bin/env python3
"""
Diagnostic script to test and verify Google Sheets CRM sync.
Run: .venv/bin/python test_crm_sync.py
"""
import os
import sys
import httpx
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

url = os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "").strip()

print("=" * 60)
print("🔍 PRAKRUTHI CRM WEBHOOK DIAGNOSTIC")
print("=" * 60)

if not url:
    print("❌ ERROR: GOOGLE_SHEET_WEBHOOK_URL is empty in .env!")
    sys.exit(1)

print(f"Target URL: {url}\n")

# 1. Test GET (Access test)
print("Step 1: Testing access permissions (GET)...")
try:
    resp = httpx.get(url, follow_redirects=True, timeout=10.0)
    print(f"  -> HTTP Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print("  ✅ Access is PUBLIC (Anyone can post) - Perfect!")
    elif resp.status_code == 403:
        print("  ❌ 403 FORBIDDEN: Google is blocking access!")
        print("     Reason: In Apps Script Deploy settings, 'Who has access' is NOT set to 'Anyone'.")
    else:
        print(f"  ⚠️ Unexpected status: {resp.status_code}")
except Exception as e:
    print(f"  ❌ Network error: {e}")

# 2. Test POST (Data push)
print("\nStep 2: Sending a test lead row to your Google Sheet (POST)...")
test_payload = {
    "timestamp": "2026-10-19 17:00:00",
    "customer_name": "Sakib (Live Test)",
    "phone_number": "6006213273",
    "destination": "Kashmir Tour Package",
    "travel_type": "Family Tour",
    "pax_count": "4",
    "budget": "Standard",
    "travel_month": "November 2026",
    "includes_seniors": "No",
    "lead_score": "HOT 🔥",
    "summary_notes": "Diagnostic lead test from terminal"
}

try:
    resp = httpx.post(url, json=test_payload, follow_redirects=True, timeout=12.0)
    print(f"  -> HTTP Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print("  🎉 SUCCESS! Check your Google Sheet right now:")
        print("     You should see the green header and Sakib's lead row!")
    else:
        print(f"  ❌ Push failed with status {resp.status_code}.")
except Exception as e:
    print(f"  ❌ Push error: {e}")

print("=" * 60)
