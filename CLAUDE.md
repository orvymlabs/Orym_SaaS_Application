# AI WhatsApp Bot with WooCommerce Integration

## Project Overview
This is a SaaS application that provides AI-powered WhatsApp bots with WooCommerce integration for e-commerce businesses.

## Architecture
- **Frontend**: Next.js application
- **Backend**: FastAPI (Python) with PostgreSQL database
- **Database**: PostgreSQL with SQLAlchemy ORM

## Key Components

### Database Models
- **User**: User accounts with role-based access (super_admin, admin, user)
- **Bot**: WhatsApp bot instances linked to users
- **BotSettings**: Bot configuration including AI model settings, templates, and messages
- **Integration**: WhatsApp and WooCommerce API credentials
- **Message**: Chat message history
- **Lead**: Customer lead tracking
- **Order**: Order management from WhatsApp conversations

### Bot Modes
- **default**: Predefined responses
- **predefined**: Template-based responses
- **ai**: AI-powered conversational bot

## Database Migrations

When adding new columns to models, create a migration script in the `backend/` directory:

```python
import psycopg2
from config import get_settings

settings = get_settings()
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()

try:
    cur.execute("""
        ALTER TABLE table_name
        ADD COLUMN IF NOT EXISTS column_name TYPE;
    """)
    conn.commit()
    print("SUCCESS: Migration completed!")
except Exception as e:
    conn.rollback()
    print(f"ERROR: Migration failed: {e}")
    raise
finally:
    cur.close()
    conn.close()
```

Run migrations with: `python migration_script.py`

## Recent Fixes

### Welcome Message Column Issue (2026-05-09)
**Problem**: Database error when saving bot settings - `column bot_settings.welcome_message does not exist`

**Root Cause**: The SQLAlchemy model defined `welcome_message` and `response_delay` columns, but they weren't present in the actual PostgreSQL database.

**Solution**: Created and ran `add_welcome_message_migration.py` to add the missing columns:
- `welcome_message` (TEXT, nullable) - Dynamic welcome/greeting message
- `response_delay` (INTEGER, default 0) - Delay in seconds before bot responds

## Development Notes
- Always sync database schema with SQLAlchemy models using migrations
- Use `ADD COLUMN IF NOT EXISTS` to make migrations idempotent
- Avoid Unicode characters in print statements on Windows (use ASCII alternatives)
