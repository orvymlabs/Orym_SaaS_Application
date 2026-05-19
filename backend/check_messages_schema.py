import sqlite3
import os
from pathlib import Path
from config import get_settings

settings = get_settings()

def check_schema():
    if settings.DATABASE_URL.startswith("postgresql"):
        print("Using PostgreSQL - skip local sqlite check")
        return

    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("PRAGMA table_info(messages)")
    columns = cur.fetchall()
    print("Columns in 'messages' table:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_schema()
