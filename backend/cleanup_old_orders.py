"""
Delete old orders that don't have order_details
"""
from database import SessionLocal
from models import Order

db = SessionLocal()

try:
    # Find orders without order_details
    old_orders = db.query(Order).filter(
        (Order.order_details == None) | (Order.order_details == '')
    ).all()

    print(f"Found {len(old_orders)} orders without details:")
    for order in old_orders:
        print(f"  - Order #{order.id} (Phone: {order.phone}, Created: {order.created_at})")

    if old_orders:
        confirm = input("\nDelete these orders? (yes/no): ")
        if confirm.lower() == 'yes':
            count = db.query(Order).filter(
                (Order.order_details == None) | (Order.order_details == '')
            ).delete()
            db.commit()
            print(f"\n✅ Deleted {count} old orders")
        else:
            print("\n❌ Cancelled")
    else:
        print("\nNo orders to delete")

except Exception as e:
    print(f"\n❌ Error: {e}")
    db.rollback()
finally:
    db.close()
