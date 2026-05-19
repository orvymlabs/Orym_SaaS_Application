import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User
from services import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_all_passwords(default_password="password123"):
    """Reset all user passwords to a default password."""
    db = SessionLocal()
    try:
        users = db.query(User).all()

        logger.info(f"Found {len(users)} users. Resetting all passwords to: {default_password}")

        for user in users:
            user.password_hash = hash_password(default_password)
            logger.info(f"Reset password for: {user.email} (Role: {user.role})")

        db.commit()
        logger.info("\n" + "="*60)
        logger.info("All passwords reset successfully!")
        logger.info("="*60)
        logger.info(f"\nDefault password for all users: {default_password}")
        logger.info("\nUser list:")

        for user in users:
            logger.info(f"  - {user.email} (Role: {user.role})")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reset passwords: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reset all user passwords.")
    parser.add_argument("--password", default="password123", help="Default password for all users")
    args = parser.parse_args()

    reset_all_passwords(args.password)
