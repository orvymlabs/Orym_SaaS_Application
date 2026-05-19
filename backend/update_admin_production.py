"""
Update admin credentials in PRODUCTION PostgreSQL database.
Run this script on Render backend or use the SQL commands below.
"""

# ===========================================
# OPTION 1: SQL Commands for Render Console
# ===========================================
# Go to Render Dashboard > PostgreSQL > Connect > PSQL
# Then run these commands:

"""
-- First, check if admin user exists
SELECT id, email, role, plan FROM users WHERE email = 'admin@orvym.com';

-- If user exists, update credentials:
UPDATE users
SET
    password_hash = '$2b$12$YourHashedPasswordHere',  -- You'll need to generate this
    role = 'super_admin',
    plan = 'growth',
    full_name = 'ORVYM Admin'
WHERE email = 'admin@orvym.com';

-- If user doesn't exist, you'll need to insert it (see Python script below)
"""

# ===========================================
# OPTION 2: Python Script for Production
# ===========================================
# Deploy this script to Render and run it there

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, init_db
from models import User, Bot, BotSettings, Integration, Usage
from services.auth_service import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_production_admin():
    """Update admin credentials in production database."""

    # Initialize database
    init_db()

    db = SessionLocal()
    try:
        # New admin credentials
        admin_email = "admin@orvym.com"
        admin_password = "admin765orvym@*"

        logger.info(f"Connecting to production database...")

        # Check if user already exists
        existing = db.query(User).filter(User.email == admin_email).first()

        if existing:
            logger.info(f"User {admin_email} found. Updating credentials...")
            existing.role = "super_admin"
            existing.password_hash = hash_password(admin_password)
            existing.full_name = "ORVYM Admin"
            existing.plan = "growth"
            db.commit()
            logger.info(f"✅ Admin credentials updated successfully in PRODUCTION!")
        else:
            logger.info(f"Creating new admin user: {admin_email}")
            # Create new super admin
            user = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="super_admin",
                full_name="ORVYM Admin",
                plan="growth"
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
            logger.info(f"✅ Admin user created successfully in PRODUCTION!")

        logger.info(f"\n{'='*60}")
        logger.info(f"PRODUCTION Admin Credentials:")
        logger.info(f"Email: {admin_email}")
        logger.info(f"Password: {admin_password}")
        logger.info(f"Role: super_admin")
        logger.info(f"Plan: growth")
        logger.info(f"Login URL: https://apps.orvym.com/login")
        logger.info(f"{'='*60}\n")

        return True

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update admin credentials: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    update_production_admin()
