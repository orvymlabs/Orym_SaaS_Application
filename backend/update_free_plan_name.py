"""
Update Free plan display name from 'Free Starter' to 'Free'.
"""
from database import SessionLocal
from models import Plan

def update_free_plan():
    db = SessionLocal()
    try:
        print("Updating Free plan display name...")

        free_plan = db.query(Plan).filter(Plan.plan_name == "free").first()

        if free_plan:
            print(f"Current display name: {free_plan.display_name}")
            free_plan.display_name = "Free"
            db.commit()
            print(f"Updated display name: {free_plan.display_name}")
            print("SUCCESS: Free plan updated!")
        else:
            print("ERROR: Free plan not found!")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_free_plan()
