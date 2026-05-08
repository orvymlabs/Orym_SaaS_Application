"""Run database migration to add order form columns"""
import psycopg2
from config import get_settings

settings = get_settings()

# Connect to database
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()

try:
    print("Adding order form columns to bot_settings table...")

    # Add columns to bot_settings
    cur.execute("""
        ALTER TABLE bot_settings
        ADD COLUMN IF NOT EXISTS order_form_template TEXT,
        ADD COLUMN IF NOT EXISTS order_confirmation_message TEXT,
        ADD COLUMN IF NOT EXISTS order_form_enabled BOOLEAN DEFAULT TRUE;
    """)

    print("Adding order_details column to orders table...")

    # Add order_details column and make other columns nullable
    cur.execute("""
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS order_details TEXT;
    """)

    cur.execute("""
        ALTER TABLE orders
        ALTER COLUMN name DROP NOT NULL,
        ALTER COLUMN address DROP NOT NULL,
        ALTER COLUMN product_name DROP NOT NULL;
    """)

    conn.commit()
    print("✅ Migration completed successfully!")

except Exception as e:
    conn.rollback()
    print(f"❌ Migration failed: {e}")
    raise
finally:
    cur.close()
    conn.close()
