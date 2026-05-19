"""
Migration: Add custom message fields to bot_settings table
Adds fallback_message, order_error_message, and error_message columns
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add custom message columns to bot_settings table."""
    db_path = "data/saas_bot.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(bot_settings)")
        columns = [col[1] for col in cursor.fetchall()]

        migrations_needed = []

        if "fallback_message" not in columns:
            migrations_needed.append("fallback_message")

        if "order_error_message" not in columns:
            migrations_needed.append("order_error_message")

        if "error_message" not in columns:
            migrations_needed.append("error_message")

        if not migrations_needed:
            logger.info("✅ All custom message columns already exist")
            return

        # Add missing columns
        for column in migrations_needed:
            logger.info(f"Adding column: {column}")
            cursor.execute(f"ALTER TABLE bot_settings ADD COLUMN {column} TEXT")

        conn.commit()
        logger.info(f"✅ Migration completed successfully. Added {len(migrations_needed)} columns.")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
