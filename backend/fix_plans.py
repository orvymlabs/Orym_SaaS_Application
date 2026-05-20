"""
Fix database plans to match the new limits.
"""
from sqlalchemy import text
from database import engine, SessionLocal
from models import Plan

def fix_plans():
    db = SessionLocal()
    try:
        print("Checking and updating plans...")
        
        # Free Plan
        free = db.query(Plan).filter(Plan.plan_name == "free").first()
        if free:
            print(f"Updating Free plan: max_templates=3, max_rule_based_messages=3")
            free.max_templates = 3
            free.max_rule_based_messages = 3
            free.max_products = 10
        
        # Starter Plan
        starter = db.query(Plan).filter(Plan.plan_name == "starter").first()
        if starter:
            print(f"Updating Starter plan: max_templates=10, max_rule_based_messages=10, price=9.99")
            starter.max_templates = 10
            starter.max_rule_based_messages = 10
            starter.monthly_price = 9.99
            starter.max_products = 100
            starter.order_form_enabled = True
            
        # Premium Plan
        premium = db.query(Plan).filter(Plan.plan_name == "premium").first()
        if premium:
            print(f"Updating Premium plan: unlimited everything")
            premium.max_templates = 0
            premium.max_rule_based_messages = 0
            premium.max_products = 0
            premium.order_form_enabled = True
            premium.multi_ai_support = True
            
        db.commit()
        print("✅ Plans updated successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to update plans: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_plans()
