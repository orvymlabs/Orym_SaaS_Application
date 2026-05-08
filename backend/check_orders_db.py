"""
Diagnostic script to check orders table structure and data
"""
import psycopg2
from config import get_settings

settings = get_settings()

# Connect to database
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()

try:
    print("=" * 60)
    print("CHECKING ORDERS TABLE STRUCTURE")
    print("=" * 60)

    # Check if order_details column exists
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'orders'
        ORDER BY ordinal_position;
    """)

    columns = cur.fetchall()
    print("\nOrders table columns:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")

    # Check if order_details column exists
    has_order_details = any(col[0] == 'order_details' for col in columns)
    if has_order_details:
        print("\n[OK] order_details column EXISTS")
    else:
        print("\n[ERROR] order_details column DOES NOT EXIST - Migration needed!")

    print("\n" + "=" * 60)
    print("CHECKING EXISTING ORDERS DATA")
    print("=" * 60)

    # Get total count
    cur.execute("SELECT COUNT(*) FROM orders;")
    total_count = cur.fetchone()[0]
    print(f"\nTotal orders in database: {total_count}")

    if total_count > 0:
        # Get recent orders
        cur.execute("""
            SELECT id, phone, name, product_name, order_details, status, created_at
            FROM orders
            ORDER BY created_at DESC
            LIMIT 5;
        """)

        orders = cur.fetchall()
        print(f"\nLast 5 orders:")
        for order in orders:
            order_id, phone, name, product_name, order_details, status, created_at = order
            print(f"\n  Order #{order_id}")
            print(f"    Phone: {phone}")
            print(f"    Name: {name}")
            print(f"    Product: {product_name}")
            print(f"    Status: {status}")
            print(f"    Created: {created_at}")
            if order_details:
                print(f"    Order Details: {order_details[:100]}...")
            else:
                print(f"    Order Details: [EMPTY] NULL or EMPTY")

        # Count orders with empty order_details
        cur.execute("""
            SELECT COUNT(*) FROM orders
            WHERE order_details IS NULL OR order_details = '';
        """)
        empty_count = cur.fetchone()[0]
        print(f"\n[WARNING] Orders with empty order_details: {empty_count} out of {total_count}")

    print("\n" + "=" * 60)
    print("CHECKING BOT_SETTINGS TABLE")
    print("=" * 60)

    # Check bot_settings columns
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'bot_settings'
        AND column_name IN ('order_form_template', 'order_confirmation_message', 'order_form_enabled')
        ORDER BY column_name;
    """)

    bot_settings_cols = cur.fetchall()
    print("\nOrder form columns in bot_settings:")
    if bot_settings_cols:
        for col in bot_settings_cols:
            print(f"  [OK] {col[0]}: {col[1]}")
    else:
        print("  [ERROR] No order form columns found - Migration needed!")

    # Check actual bot_settings data
    cur.execute("""
        SELECT id, order_form_template, order_confirmation_message, order_form_enabled
        FROM bot_settings
        LIMIT 3;
    """)

    settings_data = cur.fetchall()
    if settings_data:
        print("\nBot settings data (first 3):")
        for setting in settings_data:
            setting_id, template, confirmation, enabled = setting
            print(f"\n  Bot Settings #{setting_id}")
            print(f"    Order form enabled: {enabled}")
            print(f"    Has template: {'Yes' if template else 'No'}")
            print(f"    Has confirmation: {'Yes' if confirmation else 'No'}")

    print("\n" + "=" * 60)

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
