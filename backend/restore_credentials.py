"""
Restore default admin credentials to the database.
Run this script to reset admin password to: password123
"""
import sys
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal, init_db
from models import User, Bot, BotSettings, Integration, Usage
from services.auth_service import hash_password

def restore_admin_credentials():
    """Restore default admin user with known credentials."""

    # Initialize database
    init_db()

    db = SessionLocal()

    try:
        # Default admin credentials
        admin_email = "admin@orvym.com"
        admin_password = "password123"

        # Check if admin exists
        admin = db.query(User).filter(User.email == admin_email).first()

        if admin:
            print(f"[OK] Found existing admin user: {admin_email}")
            # Update password
            admin.password_hash = hash_password(admin_password)
            admin.role = "super_admin"
            admin.plan = "growth"
            print(f"[OK] Updated admin password and role")
        else:
            print(f"[INFO] Admin user not found. Creating new admin user...")
            # Create new admin user
            admin = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="super_admin",
                plan="growth",
                full_name="System Administrator"
            )
            db.add(admin)
            db.flush()

            # Create default bot for admin
            bot = Bot(user_id=admin.id, mode="default", status=True)
            db.add(bot)
            db.flush()

            # Create bot settings, integration, and usage
            bs = BotSettings(bot_id=bot.id)
            integ = Integration(bot_id=bot.id)
            usage = Usage(user_id=admin.id)
            db.add(bs)
            db.add(integ)
            db.add(usage)

            print(f"[OK] Created new admin user with all dependencies")

        db.commit()

        print("\n" + "="*60)
        print("[SUCCESS] CREDENTIALS RESTORED SUCCESSFULLY")
        print("="*60)
        print(f"\nEmail:    {admin_email}")
        print(f"Password: {admin_password}")
        print(f"Role:     {admin.role}")
        print(f"Plan:     {admin.plan}")
        print(f"\nYou can now login at: http://localhost:3000")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    restore_admin_credentials()
