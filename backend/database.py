"""
Database configuration with PostgreSQL production support.

Features:
- PostgreSQL for production (Render, Supabase, AWS RDS, etc.)
- SQLite fallback for development
- Connection pooling for high-traffic 24/7 bots
- Automatic reconnection on connection loss
- WAL mode for SQLite performance
"""
import logging
import sqlalchemy
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import QueuePool
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Determine database type
IS_SQLITE = "sqlite" in settings.DATABASE_URL

# Connection arguments
connect_args = {}
if IS_SQLITE:
    connect_args = {"check_same_thread": False}
    logger.info(f"Using SQLite database: {settings.DATABASE_URL.split(':///')[1]}")
else:
    logger.info(f"Using PostgreSQL database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'}")
# Engine configuration for production reliability
engine = None
try:
    if IS_SQLITE:
        # SQLite configuration
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args=connect_args,
            echo=settings.DEBUG,
            pool_pre_ping=True,  # Enable connection health checks
        )
    else:
        # PostgreSQL configuration with connection pooling for 24/7 bots
        logger.info(f"Attempting to connect to PostgreSQL...")
        engine = create_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=40,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            connect_args=connect_args,
            echo=settings.DEBUG,
        )

    # Test connection
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("SELECT 1"))
    logger.info("Database connection established successfully")

except Exception as e:
    logger.error(f"DATABASE CONNECTION FAILED: {e}")
    
    if not IS_SQLITE:
        logger.error(f"PostgreSQL connection details: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'HIDDEN'}")
    
    # Check if we should really fall back or just fail
    if settings.ENVIRONMENT == "production":
        logger.critical("PRODUCTION DATABASE CONNECTION FAILED! STOPPING TO PREVENT DATA LOSS.")
        # In production, we do NOT fall back to SQLite. We want the app to fail 
        # so the user knows the database connection is broken.
        raise RuntimeError(f"Could not connect to production database: {e}")
    
    logger.warning("FALLING BACK TO IN-MEMORY SQLITE DATABASE. All data will be lost on restart!")
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

# Session factory - MUST be bound to the finalized engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Enable foreign keys for SQLite (both explicit and fallback)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        if IS_SQLITE and ":memory:" not in str(engine.url):
            cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
        logger.debug("SQLite pragmas configured")


def get_db():
    """
    Database session dependency injection.
    Yields session and ensures cleanup after request.
    """
    db = SessionLocal()
    try:
        yield db
    except OperationalError as e:
        logger.error(f"Database operational error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def run_schema_migrations():
    """
    Add columns that are missing from existing tables.

    Base.metadata.create_all() only creates missing TABLES, it never ALTERs
    existing tables. When new columns are added to a model, this runs the
    equivalent ALTER TABLE statements so an existing production database is
    upgraded in place (no data loss).
    """
    try:
        inspector = sqlalchemy.inspect(engine)
        tables = set(inspector.get_table_names())

        migrations = {
            "integrations": [
                ("waba_id", "VARCHAR(100)"),
                ("business_id", "VARCHAR(100)"),
                ("verified_name", "VARCHAR(255)"),
                ("connection_status", "VARCHAR(50)"),
            ],
        }

        with engine.begin() as conn:
            for table, columns in migrations.items():
                if table not in tables:
                    continue
                existing = {c["name"] for c in inspector.get_columns(table)}
                for col_name, col_type in columns:
                    if col_name not in existing:
                        logger.info(f"Schema migration: adding {table}.{col_name} ({col_type})")
                        conn.execute(
                            sqlalchemy.text(
                                f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
                            )
                        )
        logger.info("Schema migrations applied successfully")
    except Exception as e:
        logger.error(f"Schema migration failed: {e}")
        # Non-fatal: the app can still boot; the affected fields stay NULL.
        # Log the full trace so it can be fixed in the deployment environment.


def init_db():
    """
    Initialize database tables.
    Ensures all models are imported so they are registered with Base.metadata.
    """
    try:
        # Import all models here to ensure they are registered with Base.metadata
        # This is CRITICAL for Base.metadata.create_all to work.
        from models import User, Plan, Subscription, Bot, BotSettings, Integration, Message, Lead, Usage, SiteInfoCache, Announcement, Order, UserTemplate, AuditLog, SystemSetting, Notification, MetaOAuthCode
        
        db_type = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"
        if ":memory:" in str(engine.url):
            db_type = "In-Memory SQLite"
            
        logger.info(f"Initializing {db_type} database tables...")
        
        # Log which models are registered
        registered_tables = list(Base.metadata.tables.keys())
        logger.debug(f"Registered tables in metadata: {registered_tables}")
        
        # Actually create the tables
        Base.metadata.create_all(bind=engine)

        # Upgrade existing tables with any newly added columns
        run_schema_migrations()
        
        # Verify tables after creation using an inspector
        inspector = sqlalchemy.inspect(engine)
        actual_tables = inspector.get_table_names()
        logger.info(f"Database tables verified/created successfully on {db_type}. Total tables: {len(actual_tables)}")
        
        if len(actual_tables) < 5:
            logger.error(f"CRITICAL: Only {len(actual_tables)} tables found after initialization! This is likely incomplete.")
            logger.error(f"Tables found: {actual_tables}")
            return False
            
        # Seed default plans if they don't exist
        seed_default_data()
        
        return True
    except Exception as e:
        logger.error(f"FAILED TO INITIALIZE DATABASE TABLES: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def seed_default_data():
    """Seed initial data like default plans if the table is empty."""
    db = SessionLocal()
    try:
        from models import Plan
        
        # Check if plans exist
        if db.query(Plan).count() == 0:
            logger.info("Seeding default plans...")
            plans = [
                Plan(
                    plan_name="free", 
                    display_name="Free Starter", 
                    monthly_price=0.0,
                    max_products=10,
                    max_templates=3,
                    max_rule_based_messages=3
                ),
                Plan(
                    plan_name="starter", 
                    display_name="Starter Bot", 
                    monthly_price=9.99,
                    max_products=100,
                    max_templates=10,
                    max_rule_based_messages=10,
                    order_form_enabled=True
                ),
                Plan(
                    plan_name="premium",
                    display_name="Premium",
                    monthly_price=0.0,
                    max_products=0,  # 0 means unlimited
                    max_templates=0,  # 0 means unlimited
                    max_rule_based_messages=0, # 0 means unlimited
                    max_ai_responses_per_session=0,  # 0 means unlimited
                    website_fetch_scope="full",
                    order_form_enabled=True,
                    multi_ai_support=True,
                    setup_support=True,
                    team_collaboration=True,
                    analytics_dashboard=True,
                    crm_integrations=True,
                    managed_api=True
                )
            ]
            db.add_all(plans)
            db.commit()
            logger.info("Default plans seeded successfully.")
    except Exception as e:
        logger.error(f"Failed to seed default data: {e}")
        db.rollback()
    finally:
        db.close()
