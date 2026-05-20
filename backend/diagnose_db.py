"""
Diagnostic script to check database connection and tables in production.
Supports both SQLite and PostgreSQL.
"""
import os
import sys
from pathlib import Path
import sqlalchemy
from sqlalchemy import create_engine, inspect, text

# Add backend directory to path
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config import get_settings
from database import engine, init_db

def diagnose():
    settings = get_settings()
    print("=" * 60)
    print("DATABASE DIAGNOSTIC")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database URL (masked): {str(engine.url).split('@')[-1] if '@' in str(engine.url) else engine.url}")
    
    try:
        # Check connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("[OK] Connection established successfully")
            
        # Inspect tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\nTables found ({len(tables)}):")
        for table in sorted(tables):
            print(f"  - {table}")
            
        required_tables = ['users', 'bots', 'bot_settings', 'integrations', 'notifications', 'orders', 'subscriptions', 'plans']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"\n[ERROR] Missing required tables: {', '.join(missing_tables)}")
            print("\nAttempting to initialize database tables...")
            success = init_db()
            if success:
                print("[OK] init_db() called successfully")
                # Re-check tables
                tables_after = inspect(engine).get_table_names()
                print(f"Tables found after initialization ({len(tables_after)}):")
                for table in sorted(tables_after):
                    print(f"  - {table}")
                
                missing_still = [t for t in required_tables if t not in tables_after]
                if not missing_still:
                    print("\n[SUCCESS] All tables created successfully!")
                else:
                    print(f"\n[STILL MISSING] {', '.join(missing_still)}")
            else:
                print("[FAILED] init_db() returned False")
        else:
            print("\n[OK] All core tables are present.")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
