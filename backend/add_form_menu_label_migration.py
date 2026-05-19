"""
Migration: Add form_menu_label column to bot_settings table
Run this once to add the new column to existing databases
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add form_menu_label column to bot_settings table"""
    try:
        conn = sqlite3.connect('whatsapp_bot.db')
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(bot_settings)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'form_menu_label' in columns:
            logger.info("✓ Column 'form_menu_label' already exists. No migration needed.")
            conn.close()
            return

        # Add the new column
        logger.info("Adding 'form_menu_label' column to bot_settings table...")
        cursor.execute("""
            ALTER TABLE bot_settings
            ADD COLUMN form_menu_label VARCHAR(30)
        """)

        conn.commit()
        logger.info("✓ Migration completed successfully!")
        logger.info("✓ Column 'form_menu_label' added to bot_settings table")

        conn.close()

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate()
