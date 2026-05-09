"""Add welcome_message and response_delay columns to bot_settings table"""
import psycopg2
from config import get_settings

settings = get_settings()

# Connect to database
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()

try:
    print("Adding welcome_message and response_delay columns to bot_settings table...")

    # Add columns to bot_settings
    cur.execute("""
        ALTER TABLE bot_settings
        ADD COLUMN IF NOT EXISTS welcome_message TEXT,
        ADD COLUMN IF NOT EXISTS response_delay INTEGER DEFAULT 0;
    """)

    conn.commit()
    print("SUCCESS: Migration completed successfully!")
    print("   - Added welcome_message column (TEXT, nullable)")
    print("   - Added response_delay column (INTEGER, default 0)")

except Exception as e:
    conn.rollback()
    print(f"ERROR: Migration failed: {e}")
    raise
finally:
    cur.close()
    conn.close()
