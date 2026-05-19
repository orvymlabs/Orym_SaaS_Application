"""
Add form_menu_label column to bot_settings table
"""
from database import SessionLocal, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_column():
    """Add form_menu_label column to bot_settings table"""
    db = SessionLocal()
    try:
        # Check if column exists
        result = db.execute(text("PRAGMA table_info(bot_settings)"))
        columns = [row[1] for row in result.fetchall()]

        if 'form_menu_label' in columns:
            logger.info("✓ Column 'form_menu_label' already exists")
            return

        # Add the column
        logger.info("Adding 'form_menu_label' column...")
        db.execute(text("ALTER TABLE bot_settings ADD COLUMN form_menu_label VARCHAR(30)"))
        db.commit()
        logger.info("✓ Column 'form_menu_label' added successfully!")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_column()
