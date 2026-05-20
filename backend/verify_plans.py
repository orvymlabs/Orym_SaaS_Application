"""
Verify plans in database after migration.
"""
from database import SessionLocal
from models import Plan

def verify_plans():
    db = SessionLocal()
    try:
        plans = db.query(Plan).all()
        print("Current plans in database:")
        print("-" * 60)
        for i, p in enumerate(plans, 1):
            print(f"{i}. {p.plan_name}: {p.display_name}")
            print(f"   Price: ${p.monthly_price}")
            print(f"   Templates: {p.max_templates} (0=unlimited)")
            print(f"   Rules: {p.max_rule_based_messages} (0=unlimited)")
            print(f"   Products: {p.max_products} (0=unlimited)")
            print(f"   Website: {p.website_fetch_scope}")
            print(f"   Managed API: {p.managed_api}")
            print()

        # Check for premium plan specifically
        premium = db.query(Plan).filter(Plan.plan_name == "premium").first()
        if premium:
            print("SUCCESS: Premium plan exists!")
            print(f"Display Name: {premium.display_name}")
            print(f"Monthly Price: ${premium.monthly_price} (shows as 'Contact Sales')")
        else:
            print("WARNING: Premium plan not found!")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_plans()
