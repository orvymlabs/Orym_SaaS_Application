"""
Check which user owns Order #7 and verify user_id mapping
"""
import psycopg2
from config import get_settings

settings = get_settings()
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()

try:
    print("Checking Order #7 ownership...")
    print("=" * 60)

    # Get Order #7 details
    cur.execute("""
        SELECT o.id, o.user_id, o.bot_id, o.phone, o.order_details, o.created_at,
               u.email, u.full_name
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        WHERE o.id = 7;
    """)

    order = cur.fetchone()
    if order:
        order_id, user_id, bot_id, phone, details, created, email, name = order
        print(f"Order #{order_id}")
        print(f"  User ID: {user_id}")
        print(f"  User Email: {email}")
        print(f"  User Name: {name}")
        print(f"  Bot ID: {bot_id}")
        print(f"  Phone: {phone}")
        print(f"  Created: {created}")
        print(f"  Has Details: {bool(details)}")
        if details:
            print(f"  Details: {details[:100]}...")
    else:
        print("Order #7 not found")

    print("\n" + "=" * 60)
    print("All users in system:")
    print("=" * 60)

    cur.execute("""
        SELECT id, email, full_name, role, plan
        FROM users
        ORDER BY id;
    """)

    users = cur.fetchall()
    for user in users:
        user_id, email, full_name, role, plan = user
        print(f"\nUser #{user_id}")
        print(f"  Email: {email}")
        print(f"  Name: {full_name}")
        print(f"  Role: {role}")
        print(f"  Plan: {plan}")

        # Count orders for this user
        cur.execute("SELECT COUNT(*) FROM orders WHERE user_id = %s", (user_id,))
        order_count = cur.fetchone()[0]
        print(f"  Orders: {order_count}")

        # Count orders with details
        cur.execute("""
            SELECT COUNT(*) FROM orders
            WHERE user_id = %s AND order_details IS NOT NULL AND order_details != ''
        """, (user_id,))
        orders_with_details = cur.fetchone()[0]
        print(f"  Orders with details: {orders_with_details}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
