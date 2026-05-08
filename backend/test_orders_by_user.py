"""
Test Orders API - Check which user's orders are returned
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import SessionLocal
from models import Order, User, Bot

def test_orders_by_user():
    db = SessionLocal()
    try:
        # Get all users
        users = db.query(User).all()
        print(f"[INFO] Total users in database: {len(users)}\n")

        for user in users:
            # Get orders for this user
            orders = db.query(Order).filter(Order.user_id == user.id).all()

            if orders:
                print(f"[USER] ID: {user.id}, Email: {user.email}, Plan: {user.plan}")
                print(f"       Orders: {len(orders)}")

                for order in orders:
                    print(f"       - Order #{order.id}: Phone {order.phone}, Status {order.status}")
                    if order.order_details:
                        preview = order.order_details[:50].replace('\n', ' ')
                        print(f"         Details: {preview}...")
                print()

        # Check if there are any orphaned orders (user_id doesn't exist)
        all_orders = db.query(Order).all()
        user_ids = {u.id for u in users}
        orphaned = [o for o in all_orders if o.user_id not in user_ids]

        if orphaned:
            print(f"[WARNING] Found {len(orphaned)} orphaned orders (user doesn't exist):")
            for order in orphaned:
                print(f"  - Order #{order.id}: user_id={order.user_id}, Phone {order.phone}")

    finally:
        db.close()

if __name__ == "__main__":
    test_orders_by_user()
