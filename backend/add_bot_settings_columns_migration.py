"""
Migration: Add missing columns to bot_settings table
Adds: order_form_template, order_confirmation_message, order_form_enabled, welcome_message, response_delay
"""
import sqlite3
import psycopg2
from config import get_settings

settings = get_settings()

def run_migration():
    """Add missing columns to bot_settings table."""

    if settings.DATABASE_URL.startswith("postgresql"):
        print("Running migration on PostgreSQL...")
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()

        try:
            cur.execute("""
                ALTER TABLE bot_settings
                ADD COLUMN IF NOT EXISTS order_form_template TEXT,
                ADD COLUMN IF NOT EXISTS order_confirmation_message TEXT,
                ADD COLUMN IF NOT EXISTS order_form_enabled BOOLEAN DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS welcome_message TEXT,
                ADD COLUMN IF NOT EXISTS response_delay INTEGER DEFAULT 0;
            """)
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
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        try:
            # Check existing columns
            cur.execute("PRAGMA table_info(bot_settings)")
            columns = [row[1] for row in cur.fetchall()]

            # Add missing columns one by one
            if "order_form_template" not in columns:
                cur.execute("ALTER TABLE bot_settings ADD COLUMN order_form_template TEXT")
                print("Added: order_form_template")

            if "order_confirmation_message" not in columns:
                cur.execute("ALTER TABLE bot_settings ADD COLUMN order_confirmation_message TEXT")
                print("Added: order_confirmation_message")

            if "order_form_enabled" not in columns:
                cur.execute("ALTER TABLE bot_settings ADD COLUMN order_form_enabled BOOLEAN DEFAULT 1")
                print("Added: order_form_enabled")

            if "welcome_message" not in columns:
                cur.execute("ALTER TABLE bot_settings ADD COLUMN welcome_message TEXT")
                print("Added: welcome_message")

            if "response_delay" not in columns:
                cur.execute("ALTER TABLE bot_settings ADD COLUMN response_delay INTEGER DEFAULT 0")
                print("Added: response_delay")

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
