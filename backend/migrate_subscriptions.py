"""
Database migration to add subscription functionality - handles existing schema

This migration safely adds new columns to existing tables without data loss.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from database import engine, SessionLocal, init_db
from models import Plan, User, Subscription
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_database():
    """Run database migrations"""
    logger.info("Starting database migration...")

    # First, ensure all tables exist
    init_db()

    with engine.connect() as conn:
        try:
            # Add missing columns to plans table
            logger.info("Checking plans table schema...")

            plans_migrations = [
                ("display_name", "ALTER TABLE plans ADD COLUMN display_name VARCHAR(50)"),
                ("max_rule_based_messages", "ALTER TABLE plans ADD COLUMN max_rule_based_messages INTEGER DEFAULT 0"),
                ("max_ai_responses_per_session", "ALTER TABLE plans ADD COLUMN max_ai_responses_per_session INTEGER DEFAULT 0"),
                ("max_products", "ALTER TABLE plans ADD COLUMN max_products INTEGER DEFAULT 0"),
                ("website_fetch_scope", "ALTER TABLE plans ADD COLUMN website_fetch_scope VARCHAR(20) DEFAULT 'homepage'"),
                ("order_form_enabled", "ALTER TABLE plans ADD COLUMN order_form_enabled BOOLEAN DEFAULT 0"),
                ("multi_ai_support", "ALTER TABLE plans ADD COLUMN multi_ai_support BOOLEAN DEFAULT 0"),
                ("setup_support", "ALTER TABLE plans ADD COLUMN setup_support BOOLEAN DEFAULT 0"),
                ("team_collaboration", "ALTER TABLE plans ADD COLUMN team_collaboration BOOLEAN DEFAULT 0"),
                ("analytics_dashboard", "ALTER TABLE plans ADD COLUMN analytics_dashboard BOOLEAN DEFAULT 0"),
                ("crm_integrations", "ALTER TABLE plans ADD COLUMN crm_integrations BOOLEAN DEFAULT 0"),
                ("managed_api", "ALTER TABLE plans ADD COLUMN managed_api BOOLEAN DEFAULT 0"),
                ("stripe_price_id", "ALTER TABLE plans ADD COLUMN stripe_price_id VARCHAR(100)"),
            ]

            for column_name, sql in plans_migrations:
                if not column_exists("plans", column_name):
                    logger.info(f"Adding column {column_name} to plans table...")
                    conn.execute(text(sql))
                    conn.commit()
                else:
                    logger.info(f"Column {column_name} already exists in plans table")

            # Add missing columns to users table
            logger.info("Checking users table schema...")

            if not column_exists("users", "stripe_customer_id"):
                logger.info("Adding stripe_customer_id to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(100)"))
                conn.commit()
            else:
                logger.info("Column stripe_customer_id already exists in users table")

            logger.info("Schema migration completed successfully!")

        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            conn.rollback()
            raise

    # Now seed/update plan data
    db = SessionLocal()
    try:
        existing_plans = db.query(Plan).count()

        if existing_plans == 0:
            logger.info("Seeding initial plan data...")
            seed_plans(db)
        else:
            logger.info(f"Found {existing_plans} existing plans. Updating...")
            update_existing_plans(db)

        # Create default subscriptions for existing users
        create_default_subscriptions(db)

        logger.info("Migration completed successfully!")

    except Exception as e:
        logger.error(f"Data migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def seed_plans(db):
    """Seed initial plan data according to CLAUDE.md"""

    plans = [
        {
            "plan_name": "free",
            "display_name": "FREE",
            "monthly_price": 0.0,
            "yearly_price": 0.0,
            "max_templates": 3,
            "max_rule_based_messages": 3,
            "max_ai_responses_per_session": 5,
            "max_products": 3,
            "website_fetch_scope": "homepage",
            "order_form_enabled": False,
            "multi_ai_support": False,
            "setup_support": False,
            "team_collaboration": False,
            "analytics_dashboard": False,
            "crm_integrations": False,
            "managed_api": False,
            "is_active": True,
        },
        {
            "plan_name": "starter",
            "display_name": "STARTER",
            "monthly_price": 9.99,
            "yearly_price": 99.99,
            "max_templates": 10,
            "max_rule_based_messages": 10,
            "max_ai_responses_per_session": 0,  # unlimited
            "max_products": 0,  # unlimited
            "website_fetch_scope": "homepage",
            "order_form_enabled": True,
            "multi_ai_support": True,
            "setup_support": True,
            "team_collaboration": False,
            "analytics_dashboard": False,
            "crm_integrations": False,
            "managed_api": False,
            "is_active": True,
        },
        {
            "plan_name": "premium",
            "display_name": "PREMIUM",
            "monthly_price": 0.0,  # Contact sales
            "yearly_price": 0.0,  # Contact sales
            "max_templates": 0,  # unlimited
            "max_rule_based_messages": 0,  # unlimited
            "max_ai_responses_per_session": 0,  # unlimited
            "max_products": 0,  # unlimited
            "website_fetch_scope": "full",
            "order_form_enabled": True,
            "multi_ai_support": True,
            "setup_support": True,
            "team_collaboration": True,
            "analytics_dashboard": True,
            "crm_integrations": True,
            "managed_api": True,
            "is_active": True,
        }
    ]

    for plan_data in plans:
        plan = Plan(**plan_data)
        db.add(plan)
        logger.info(f"Created plan: {plan_data['display_name']}")

    db.commit()
    logger.info("Plans seeded successfully!")


def update_existing_plans(db):
    """Update existing plans with new structure"""

    plan_updates = {
        "free": {
            "display_name": "FREE",
            "max_templates": 3,
            "max_rule_based_messages": 3,
            "max_ai_responses_per_session": 5,
            "max_products": 3,
            "website_fetch_scope": "homepage",
            "order_form_enabled": False,
            "multi_ai_support": False,
            "setup_support": False,
            "team_collaboration": False,
            "analytics_dashboard": False,
            "crm_integrations": False,
            "managed_api": False,
        },
        "starter": {
            "display_name": "STARTER",
            "monthly_price": 9.99,
            "max_templates": 10,
            "max_rule_based_messages": 10,
            "max_ai_responses_per_session": 0,
            "max_products": 0,
            "website_fetch_scope": "homepage",
            "order_form_enabled": True,
            "multi_ai_support": True,
            "setup_support": True,
            "team_collaboration": False,
            "analytics_dashboard": False,
            "crm_integrations": False,
            "managed_api": False,
        },
        "premium": {
            "display_name": "PREMIUM",
            "max_templates": 0,
            "max_rule_based_messages": 0,
            "max_ai_responses_per_session": 0,
            "max_products": 0,
            "website_fetch_scope": "full",
            "order_form_enabled": True,
            "multi_ai_support": True,
            "setup_support": True,
            "team_collaboration": True,
            "analytics_dashboard": True,
            "crm_integrations": True,
            "managed_api": True,
        }
    }

    for plan_name, updates in plan_updates.items():
        plan = db.query(Plan).filter(Plan.plan_name == plan_name).first()
        if plan:
            for key, value in updates.items():
                setattr(plan, key, value)
            logger.info(f"Updated plan: {plan_name}")
        else:
            # Create plan if it doesn't exist
            logger.info(f"Creating missing plan: {plan_name}")
            plan_data = updates.copy()
            plan_data["plan_name"] = plan_name
            plan_data["is_active"] = True
            if plan_name == "free":
                plan_data["monthly_price"] = 0.0
                plan_data["yearly_price"] = 0.0
            elif plan_name == "premium":
                plan_data["monthly_price"] = 0.0
                plan_data["yearly_price"] = 0.0
            plan = Plan(**plan_data)
            db.add(plan)

    db.commit()


def create_default_subscriptions(db):
    """Create default FREE subscriptions for users without one"""

    free_plan = db.query(Plan).filter(Plan.plan_name == "free").first()
    if not free_plan:
        logger.error("FREE plan not found!")
        return

    users_without_subscription = db.query(User).outerjoin(Subscription).filter(
        Subscription.id == None
    ).all()

    for user in users_without_subscription:
        subscription = Subscription(
            user_id=user.id,
            plan_id=free_plan.id,
            status="active",
            billing_cycle="monthly",
        )
        db.add(subscription)
        logger.info(f"Created FREE subscription for user {user.email}")

    db.commit()
    logger.info(f"Created {len(users_without_subscription)} default subscriptions")


if __name__ == "__main__":
    migrate_database()
