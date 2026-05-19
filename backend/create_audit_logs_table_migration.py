"""
Migration: Create audit_logs table
"""
import psycopg2
import sqlite3
from config import get_settings

settings = get_settings()

def run_migration():
    """Create audit_logs table."""

    # Check if using PostgreSQL or SQLite
    if settings.DATABASE_URL.startswith("postgresql"):
        print("Running migration on PostgreSQL...")
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()

        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    action VARCHAR(100) NOT NULL,
                    target_type VARCHAR(50),
                    target_id VARCHAR(100),
                    details JSONB,
                    ip_address VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action VARCHAR(100) NOT NULL,
                    target_type VARCHAR(50),
                    target_id VARCHAR(100),
                    details JSON,
                    ip_address VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                );
            """)
            conn.commit()
            print("SUCCESS: Created 'audit_logs' table on SQLite!")

        except Exception as e:
            conn.rollback()
            print(f"ERROR: Migration failed: {e}")
            raise
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    run_migration()
