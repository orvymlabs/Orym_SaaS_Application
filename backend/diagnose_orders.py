"""
Comprehensive Orders Diagnostic
This script helps diagnose why orders might not be showing on the orders page.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import SessionLocal
from models import Order, User, Bot, Integration

def diagnose_orders_issue():
    db = SessionLocal()
    try:
        print("="*70)
        print("ORDERS PAGE DIAGNOSTIC")
        print("="*70)

        # 1. Check all users with orders
        print("\n[1] USERS WITH ORDERS:")
        print("-" * 70)

        users = db.query(User).all()
        users_with_orders = []

        for user in users:
            orders = db.query(Order).filter(Order.user_id == user.id).all()
            if orders:
                users_with_orders.append({
                    'user': user,
                    'orders': orders
                })

                print(f"\nUser: {user.email} (ID: {user.id})")
                print(f"Plan: {user.plan}")
                print(f"Total Orders: {len(orders)}")

                # Get bot info
                bot = db.query(Bot).filter(Bot.user_id == user.id).first()
                if bot:
                    integ = db.query(Integration).filter(Integration.bot_id == bot.id).first()
                    print(f"Bot ID: {bot.id}")
                    if integ and integ.whatsapp_number:
                        print(f"WhatsApp Number: {integ.whatsapp_number}")

                # Show recent orders
                print(f"\nRecent Orders:")
                for order in orders[-3:]:  # Last 3 orders
                    print(f"  - Order #{order.id}")
                    print(f"    Phone: {order.phone}")
                    print(f"    Status: {order.status}")
                    print(f"    Created: {order.created_at}")
                    if order.order_details:
                        preview = order.order_details[:60].replace('\n', ' ')
                        print(f"    Details: {preview}...")

        # 2. Check for recent orders (last 24 hours)
        print("\n\n[2] RECENT ORDERS (ALL USERS):")
        print("-" * 70)

        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)

        recent_orders = db.query(Order).filter(Order.created_at >= yesterday).order_by(Order.created_at.desc()).all()

        if recent_orders:
            print(f"\nFound {len(recent_orders)} orders in the last 24 hours:\n")
            for order in recent_orders:
                user = db.query(User).filter(User.id == order.user_id).first()
                print(f"Order #{order.id}:")
                print(f"  User: {user.email if user else 'UNKNOWN'} (ID: {order.user_id})")
                print(f"  Phone: {order.phone}")
                print(f"  Created: {order.created_at}")
                print(f"  Status: {order.status}")
                print()
        else:
            print("\nNo orders created in the last 24 hours.")

        # 3. Instructions for user
        print("\n[3] TROUBLESHOOTING STEPS:")
        print("-" * 70)
        print("\nTo see your orders on the Orders page:")
        print("\n1. Check which email you are logged in with")
        print("   - Look at the top right corner of the dashboard")
        print("\n2. Verify that email matches one of the users above who have orders")
        print("\n3. If you're logged in as a different user:")
        print("   - The orders belong to the WhatsApp bot owner")
        print("   - Make sure you're logged in with the correct account")
        print("\n4. If you just placed an order:")
        print("   - Refresh the Orders page (F5 or Ctrl+R)")
        print("   - Check if the order appears in the list above")
        print("\n5. If the order is in the database but not showing:")
        print("   - Open browser console (F12)")
        print("   - Go to Orders page")
        print("   - Check for any API errors")
        print("   - Look for the API call to /api/orders")

        print("\n" + "="*70)

    finally:
        db.close()

if __name__ == "__main__":
    diagnose_orders_issue()
