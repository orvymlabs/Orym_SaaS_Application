"""
Test the Orders API endpoint directly
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import User
from services.auth import create_access_token

def test_orders_endpoint():
    db = SessionLocal()
    try:
        # Get user royalplastics@gmail.com who has 4 orders
        user = db.query(User).filter(User.email == 'royalplastics@gmail.com').first()
        
        if not user:
            print("[ERROR] User not found")
            return
        
        print(f"[TEST USER] {user.email} (ID: {user.id})")
        
        # Create a JWT token for this user
        token = create_access_token({"sub": str(user.id)})
        print(f"[TOKEN] Generated JWT token")
        
        # Create test client
        client = TestClient(app)
        
        # Call the orders endpoint
        print("\n[API CALL] GET /api/orders")
        response = client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"[RESPONSE] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            orders = response.json()
            print(f"[RESPONSE] Orders returned: {len(orders)}")
            
            for order in orders:
                print(f"\n  Order #{order['id']}:")
                print(f"    Phone: {order['phone']}")
                print(f"    Status: {order['status']}")
                print(f"    Created: {order['created_at']}")
                if order.get('order_details'):
                    preview = order['order_details'][:50].replace('\n', ' ')
                    print(f"    Details: {preview}...")
                else:
                    print(f"    Details: [EMPTY]")
        else:
            print(f"[ERROR] {response.text}")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_orders_endpoint()
