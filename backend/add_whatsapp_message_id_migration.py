"""
Migration: Add whatsapp_message_id to messages table
"""
import psycopg2
import sqlite3
from config import get_settings

settings = get_settings()

def run_migration():
    """Add whatsapp_message_id column to messages table."""

    # Check if using PostgreSQL or SQLite
    if settings.DATABASE_URL.startswith("postgresql"):
        print("Running migration on PostgreSQL...")
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()

        try:
            # Check if column exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='messages' AND column_name='whatsapp_message_id'
            """)
            if not cur.fetchone():
                print("Adding whatsapp_message_id to messages table...")
                cur.execute("ALTER TABLE messages ADD COLUMN whatsapp_message_id VARCHAR(100)")
                cur.execute("CREATE INDEX IF NOT EXISTS ix_messages_whatsapp_message_id ON messages (whatsapp_message_id)")
            else:
                print("Column whatsapp_message_id already exists.")
            
            conn.commit()
            print("SUCCESS: Migration completed on PostgreSQL!")
        except Exception as e:
            conn.rollback()
            print(f"ERROR: Migration failed: {e}")
            raise
        finally:
            cur.close()
            conn.close()

    else:
        print("Running migration on SQLite...")
        # Extract database path from SQLite URL
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        try:
            # Check if column exists
            cur.execute("PRAGMA table_info(messages)")
            columns = [info[1] for info in cur.fetchall()]
            
            if 'whatsapp_message_id' not in columns:
                print("Adding whatsapp_message_id to messages table...")
                cur.execute("ALTER TABLE messages ADD COLUMN whatsapp_message_id VARCHAR(100)")
                cur.execute("CREATE INDEX IF NOT EXISTS ix_messages_whatsapp_message_id ON messages (whatsapp_message_id)")
            else:
                print("Column whatsapp_message_id already exists.")
                
            conn.commit()
            print("SUCCESS: Migration completed on SQLite!")

        except Exception as e:
            conn.rollback()
            print(f"ERROR: Migration failed: {e}")
            raise
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    run_migration()
