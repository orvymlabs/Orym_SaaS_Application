"""
Verify credentials in the database and test password verification.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal, init_db
from models import User
from services.auth_service import verify_password, hash_password

def verify_credentials():
    """Check all users and verify password hashing."""

    init_db()
    db = SessionLocal()

    try:
        # Get all users
        users = db.query(User).all()

        print("\n" + "="*60)
        print("DATABASE USERS")
        print("="*60)

        for user in users:
            print(f"\nID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Plan: {user.plan}")
            print(f"Password Hash: {user.password_hash[:50]}...")

            # Test password verification
            test_password = "password123"
            is_valid = verify_password(test_password, user.password_hash)
            print(f"Password 'password123' valid: {is_valid}")

            if user.email == "admin@orvym.com":
                print("\n[ADMIN ACCOUNT FOUND]")
                print(f"Testing login with: admin@orvym.com / password123")
                print(f"Verification result: {is_valid}")

                if not is_valid:
                    print("\n[WARNING] Password verification FAILED!")
                    print("Generating new hash for comparison...")
                    new_hash = hash_password(test_password)
                    print(f"New hash: {new_hash[:50]}...")
                    print(f"Current hash: {user.password_hash[:50]}...")

        print("\n" + "="*60)
        print(f"Total users in database: {len(users)}")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_credentials()
