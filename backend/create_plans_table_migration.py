"""
Migration: Create plans table
"""
import psycopg2
import sqlite3
from config import get_settings

settings = get_settings()

def run_migration():
    """Create plans table."""

    # Check if using PostgreSQL or SQLite
    if settings.DATABASE_URL.startswith("postgresql"):
        print("Running migration on PostgreSQL...")
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()

        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    id SERIAL PRIMARY KEY,
                    plan_name VARCHAR(50) UNIQUE NOT NULL,
                    monthly_price FLOAT DEFAULT 0.0,
                    yearly_price FLOAT,
                    daily_message_limit INTEGER DEFAULT 0,
                    max_templates INTEGER DEFAULT 0,
                    max_custom_order_fields INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insert default plans if they don't exist
            cur.execute("SELECT COUNT(*) FROM plans")
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute("""
                    INSERT INTO plans (plan_name, monthly_price, daily_message_limit, max_templates, max_custom_order_fields)
                    VALUES 
                    ('free', 0.0, 250, 3, 5),
                    ('starter', 29.0, 1000, 10, 20),
                    ('growth', 99.0, 0, 0, 0)
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
                CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_name VARCHAR(50) UNIQUE NOT NULL,
                    monthly_price FLOAT DEFAULT 0.0,
                    yearly_price FLOAT,
                    daily_message_limit INTEGER DEFAULT 0,
                    max_templates INTEGER DEFAULT 0,
                    max_custom_order_fields INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insert default plans if they don't exist
            cur.execute("SELECT COUNT(*) FROM plans")
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute("""
                    INSERT INTO plans (plan_name, monthly_price, daily_message_limit, max_templates, max_custom_order_fields)
                    VALUES 
                    ('free', 0.0, 250, 3, 5),
                    ('starter', 29.0, 1000, 10, 20),
                    ('growth', 99.0, 0, 0, 0)
                """)
                
            conn.commit()
            print("SUCCESS: Created 'plans' table on SQLite!")

        except Exception as e:
            conn.rollback()
            print(f"ERROR: Migration failed: {e}")
            raise
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    run_migration()
