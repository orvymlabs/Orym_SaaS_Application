"""
Migration: Add 'plan' column to users table
This column is required for the pricing plan feature (free, starter, growth)
"""
import psycopg2
import sqlite3
from config import get_settings

settings = get_settings()

def run_migration():
    """Add plan column to users table."""

    # Check if using PostgreSQL or SQLite
    if settings.DATABASE_URL.startswith("postgresql"):
        print("Running migration on PostgreSQL...")
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()

        try:
            cur.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS plan VARCHAR(20) DEFAULT 'free';
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
        # Extract database path from SQLite URL
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        try:
            # Check if column exists
            cur.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cur.fetchall()]

            if "plan" not in columns:
                cur.execute("""
                    ALTER TABLE users
                    ADD COLUMN plan VARCHAR(20) DEFAULT 'free';
                """)
                conn.commit()
                print("SUCCESS: Added 'plan' column to users table!")
            else:
                print("INFO: 'plan' column already exists, skipping.")

        except Exception as e:
            conn.rollback()
            print(f"ERROR: Migration failed: {e}")
            raise
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    run_migration()
