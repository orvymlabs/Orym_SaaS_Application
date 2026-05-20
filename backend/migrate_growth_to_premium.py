"""
Migrate growth plan to premium plan.
"""
from database import SessionLocal
from models import Plan, User, Subscription

def migrate_growth_to_premium():
    db = SessionLocal()
    try:
        print("Starting migration from 'growth' to 'premium'...")

        # Find the growth plan
        growth_plan = db.query(Plan).filter(Plan.plan_name == "growth").first()

        if growth_plan:
            print(f"Found growth plan (ID: {growth_plan.id})")

            # Update the plan
            growth_plan.plan_name = "premium"
            growth_plan.display_name = "Premium"
            growth_plan.monthly_price = 0.0  # Contact Sales
            growth_plan.max_templates = 0  # Unlimited
            growth_plan.max_rule_based_messages = 0  # Unlimited
            growth_plan.max_ai_responses_per_session = 0  # Unlimited
            growth_plan.max_products = 0  # Unlimited
            growth_plan.website_fetch_scope = "full"
            growth_plan.order_form_enabled = True
            growth_plan.multi_ai_support = True
            growth_plan.setup_support = True
            growth_plan.team_collaboration = True
            growth_plan.analytics_dashboard = True
            growth_plan.crm_integrations = True
            growth_plan.managed_api = True

            # Update users with growth plan
            users_updated = db.query(User).filter(User.plan == "growth").update(
                {"plan": "premium"}, synchronize_session=False
            )

            db.commit()
            print(f"SUCCESS: Plan migrated to 'premium'")
            print(f"  - Plan name: {growth_plan.plan_name}")
            print(f"  - Display name: {growth_plan.display_name}")
            print(f"  - Monthly price: ${growth_plan.monthly_price}")
            print(f"  - Users updated: {users_updated}")
        else:
            print("No 'growth' plan found. Checking if 'premium' already exists...")
            premium_plan = db.query(Plan).filter(Plan.plan_name == "premium").first()
            if premium_plan:
                print("Premium plan already exists. Migration not needed.")
            else:
                print("Neither 'growth' nor 'premium' plan found. Please run database seeding.")

        db.close()
        print("Migration completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"ERROR: Failed to migrate: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_growth_to_premium()
