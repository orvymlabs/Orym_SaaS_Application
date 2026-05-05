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
    logger.warning("FALLING BACK TO IN-MEMORY SQLITE DATABASE. All data will be lost on restart!")
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
# Session factory - MUST be bound to the finalized engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Enable foreign keys for SQLite (both explicit and fallback)
if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        if not IS_SQLITE: # If it's the in-memory fallback
            pass # WAL mode might not be needed for in-memory
        else:
            cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
    logger.info("SQLite pragmas configured")


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


def init_db():
    """
    Initialize database tables.
    Ensures all models are imported so they are registered with Base.metadata.
    """
    try:
        # Import all models here to ensure they are registered with Base.metadata
        from models import User, Bot, BotSettings, Integration, Message, Lead, Usage, SiteInfoCache, Announcement, Order
        
        db_type = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"
        logger.info(f"Initializing {db_type} database tables...")
        
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database tables verified/created successfully on {db_type}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        return False
