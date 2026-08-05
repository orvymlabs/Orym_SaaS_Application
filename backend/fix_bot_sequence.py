"""
Fix the bots table sequence to prevent duplicate key errors
"""
import sys
from sqlalchemy import text
from database import engine, SessionLocal

def fix_bot_sequence():
    """Reset the bots_id_seq to the correct value"""
    db = SessionLocal()
    try:
        # Get the current max id from bots table
        result = db.execute(text("SELECT MAX(id) FROM bots")).fetchone()
        max_id = result[0] if result[0] is not None else 0

        print(f"Current max ID in bots table: {max_id}")

        # Set the sequence to max_id + 1
        next_id = max_id + 1
        db.execute(text(f"SELECT setval('bots_id_seq', {next_id}, false)"))
        db.commit()

        print(f"[SUCCESS] Successfully reset bots_id_seq to {next_id}")

        # Verify the fix
        verify_result = db.execute(text("SELECT last_value FROM bots_id_seq")).fetchone()
        print(f"Sequence last_value is now: {verify_result[0]}")

    except Exception as e:
        print(f"[ERROR] Error fixing sequence: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("Fixing bots table sequence...")
    fix_bot_sequence()
