from database import SessionLocal
from models import Plan
from datetime import datetime

def reproduce():
    db = SessionLocal()
    try:
        print("Querying plans...")
        plans = db.query(Plan).all()
        print(f"Successfully queried {len(plans)} plans.")
        for p in plans:
            print(f"Plan {p.plan_name}: created_at={p.created_at}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reproduce()
