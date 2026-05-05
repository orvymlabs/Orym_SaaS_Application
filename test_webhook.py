"""
Test script to verify webhook verification endpoint works correctly.
Run this AFTER starting your backend server.
"""
import requests

# Change this to your ngrok URL
NGROK_URL = "http://localhost:8000"  # Use localhost for direct testing

webhook_url = f"{NGROK_URL}/webhook"

# Test parameters (simulate Meta's verification request)
params = {
    "hub.mode": "subscribe",
    "hub.verify_token": "testtoken123",
    "hub.challenge": "challenge_string_from_meta"
}

print(f"Testing webhook verification at: {webhook_url}")
print(f"Parameters: {params}")
print()

try:
    response = requests.get(webhook_url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    if response.status_code == 200 and "challenge_string_from_meta" in response.text:
        print("\n✓ SUCCESS: Webhook verification is working!")
    else:
        print("\n✗ FAILED: Webhook verification did not return expected challenge")
except requests.exceptions.ConnectionError:
    print("\n✗ ERROR: Could not connect to server. Is your backend running?")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
