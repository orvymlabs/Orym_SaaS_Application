"""
Migration: Create system_settings table
"""
import psycopg2
import sqlite3
import json
from config import get_settings

settings = get_settings()

def run_migration():
    """Create system_settings table."""

    # Check if using PostgreSQL or SQLite
    if settings.DATABASE_URL.startswith("postgresql"):
        print("Running migration on PostgreSQL...")
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()

        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value JSONB NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insert default settings
            defaults = {
                "platform_name": "ORVYN",
                "maintenance_mode": False,
                "allow_registrations": True,
                "default_plan": "free"
            }
            
            for k, v in defaults.items():
                cur.execute("INSERT INTO system_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING", (k, json.dumps(v)))
            
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
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value JSON NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insert default settings
            defaults = {
                "platform_name": "ORVYN",
                "maintenance_mode": False,
                "allow_registrations": True,
                "default_plan": "free"
            }
            
            for k, v in defaults.items():
                cur.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)", (k, json.dumps(v)))
                
            conn.commit()
            print("SUCCESS: Created 'system_settings' table on SQLite!")

        except Exception as e:
            conn.rollback()
            print(f"ERROR: Migration failed: {e}")
            raise
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    run_migration()
