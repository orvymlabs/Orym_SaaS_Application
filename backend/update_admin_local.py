"""
Update admin credentials in local SQLite database.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Bot, BotSettings, Integration, Usage
from services.auth_service import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use local SQLite database directly
BACKEND_DIR = Path(__file__).parent.resolve()
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "saas_bot.db"

def update_admin_credentials():
    """Update admin credentials in local SQLite database."""

    if not DB_PATH.exists():
        logger.error(f"Database file not found: {DB_PATH}")
        return False

    # Create engine for local SQLite
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        # New admin credentials
        admin_email = "admin@orvym.com"
        admin_password = "admin765orvym@*"

        # Check if user already exists
        existing = db.query(User).filter(User.email == admin_email).first()

        if existing:
            logger.info(f"User {admin_email} already exists. Updating credentials...")
            existing.role = "super_admin"
            existing.password_hash = hash_password(admin_password)
            existing.full_name = "ORVYM Admin"
            existing.plan = "premium"
            db.commit()
            logger.info(f"✅ Admin credentials updated successfully!")
        else:
            logger.info(f"Creating new admin user: {admin_email}")
            # Create new super admin
            user = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="super_admin",
                full_name="ORVYM Admin",
                plan="premium"
            )
            db.add(user)
            db.flush()

            # Create default bot for user
            bot = Bot(user_id=user.id, mode="ai", status=True)
            db.add(bot)
            db.flush()

            # Add related records
            db.add(BotSettings(bot_id=bot.id))
            db.add(Integration(bot_id=bot.id))
            db.add(Usage(user_id=user.id))

            db.commit()
            logger.info(f"✅ Admin user created successfully!")

        logger.info(f"\n{'='*50}")
        logger.info(f"Admin Credentials:")
        logger.info(f"Email: {admin_email}")
        logger.info(f"Password: {admin_password}")
        logger.info(f"Role: super_admin")
        logger.info(f"Plan: premium")
        logger.info(f"{'='*50}\n")

        return True

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update admin credentials: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    update_admin_credentials()
