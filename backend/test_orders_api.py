"""
Test the orders API endpoint to verify it returns order_details
"""
import requests
import json

# You'll need to replace this with a valid auth token
# Get it from browser dev tools or login response
AUTH_TOKEN = "YOUR_AUTH_TOKEN_HERE"

BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

try:
    print("Testing GET /api/orders endpoint...")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/orders", headers=headers)

    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")

    if response.status_code == 200:
        orders = response.json()
        print(f"Total orders returned: {len(orders)}")

        for order in orders[:3]:  # Show first 3
            print(f"\n--- Order #{order.get('id')} ---")
            print(f"Phone: {order.get('phone')}")
            print(f"Status: {order.get('status')}")
            print(f"Created: {order.get('created_at')}")

            order_details = order.get('order_details')
            if order_details:
                print(f"Order Details (length: {len(order_details)}):")
                print(f"  {order_details[:200]}...")
            else:
                print("Order Details: [EMPTY]")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Error: {e}")
    print("\nNote: Make sure:")
    print("1. Backend server is running on localhost:8000")
    print("2. You've replaced AUTH_TOKEN with a valid token")
