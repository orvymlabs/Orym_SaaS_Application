"""
Complete end-to-end test of order details flow
"""
import psycopg2
from config import get_settings
import json

settings = get_settings()

print("=" * 70)
print("COMPLETE ORDER DETAILS FLOW TEST")
print("=" * 70)

# Step 1: Check Database
print("\n[STEP 1] Checking Database...")
print("-" * 70)

conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    SELECT id, phone, order_details, status, created_at
    FROM orders
    WHERE order_details IS NOT NULL AND order_details != ''
    ORDER BY created_at DESC
    LIMIT 3;
""")

orders_with_details = cur.fetchall()

if orders_with_details:
    print(f"[OK] Found {len(orders_with_details)} orders with details in database:")
    for order in orders_with_details:
        order_id, phone, details, status, created = order
        print(f"\n  Order #{order_id}")
        print(f"    Phone: {phone}")
        print(f"    Status: {status}")
        print(f"    Created: {created}")
        print(f"    Details length: {len(details)} characters")
        print(f"    Details preview: {details[:100]}...")
else:
    print("[ERROR] No orders with details found in database!")
    print("This means new orders are not being saved correctly.")

cur.close()
conn.close()

# Step 2: Test API Response Format
print("\n\n[STEP 2] Testing API Response Format...")
print("-" * 70)

from database import SessionLocal
from models import Order, User

db = SessionLocal()

try:
    # Get a user to test with
    user = db.query(User).first()
    if not user:
        print("[ERROR] No users found in database")
    else:
        print(f"[OK] Testing with user ID: {user.id}")

        # Simulate what the API does
        orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(3).all()

        print(f"[OK] Found {len(orders)} orders for this user")

        # Format like the API does
        formatted_orders = []
        for order in orders:
            formatted = {
                "id": order.id,
                "phone": order.phone,
                "order_details": order.order_details,
                "status": getattr(order, 'status', 'Pending'),
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
            formatted_orders.append(formatted)

            print(f"\n  Order #{order.id}:")
            print(f"    Has order_details: {bool(order.order_details)}")
            if order.order_details:
                print(f"    Details length: {len(order.order_details)}")
                print(f"    Details preview: {order.order_details[:80]}...")
            else:
                print(f"    Details: [EMPTY]")

        # Show JSON format
        print("\n[OK] API Response Format (JSON):")
        print(json.dumps(formatted_orders, indent=2, default=str)[:500] + "...")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

# Step 3: Frontend Checklist
print("\n\n[STEP 3] Frontend Verification Checklist")
print("-" * 70)
print("""
To verify the frontend is working:

1. Open your Orders page in browser
2. Open Developer Tools (F12) → Console tab
3. Look for these logs:
   - "📦 Orders API Response: [...]"
   - "📦 Total orders received: X"
   - "📦 Order #X: { ... order_details_length: ... }"

4. Check the logs:
   ✓ If order_details_length > 0 → Data is reaching frontend
   ✗ If order_details_length = 0 → Check which order ID it is

5. On the page itself:
   - Orders WITH details should show the filled form text
   - Orders WITHOUT details should show:
     "No order details available for this order.
      This order was created before the order form feature was implemented."

6. If Order #7 (or any order with details in database) shows as empty:
   - Check browser console for errors
   - Check Network tab → /api/orders response
   - Verify the order_details field is in the JSON response
""")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
