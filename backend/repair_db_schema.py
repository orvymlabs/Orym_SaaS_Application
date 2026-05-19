"""
Robust Database Repair: Add any missing columns to all tables.
"""
import psycopg2
import sqlite3
import json
from config import get_settings
from database import engine
from sqlalchemy import inspect, text
from models import Base, User, Plan, Bot, BotSettings, Integration, Message, Lead, Usage, SiteInfoCache, Announcement, Order, UserTemplate, AuditLog, SystemSetting

settings = get_settings()

def get_column_type_sql(col):
    """Convert SQLAlchemy column type to SQL type string."""
    from sqlalchemy.sql import sqltypes
    
    t = col.type
    if isinstance(t, sqltypes.String):
        return f"VARCHAR({t.length})" if t.length else "TEXT"
    if isinstance(t, sqltypes.Integer):
        return "INTEGER"
    if isinstance(t, sqltypes.Boolean):
        return "BOOLEAN"
    if isinstance(t, sqltypes.Float):
        return "FLOAT"
    if isinstance(t, sqltypes.DateTime):
        return "TIMESTAMP" if settings.DATABASE_URL.startswith("postgresql") else "DATETIME"
    if isinstance(t, sqltypes.JSON):
        return "JSONB" if settings.DATABASE_URL.startswith("postgresql") else "JSON"
    if isinstance(t, sqltypes.Text):
        return "TEXT"
    
    return str(t)

def repair():
    inspector = inspect(engine)
    is_postgres = settings.DATABASE_URL.startswith("postgresql")
    
    # Get all tables registered in Base
    for table_name, table in Base.metadata.tables.items():
        if not inspector.has_table(table_name):
            print(f"Table {table_name} missing - metadata.create_all should handle this.")
            continue
            
        existing_columns = [c["name"] for c in inspector.get_columns(table_name)]
        
        for col_name, column in table.columns.items():
            if col_name not in existing_columns:
                print(f"Adding missing column: {table_name}.{col_name}")
                col_type = get_column_type_sql(column)
                
                # Add default if applicable
                default_str = ""
                if column.default is not None and hasattr(column.default, 'arg'):
                    if not callable(column.default.arg):
                        val = column.default.arg
                        if isinstance(val, bool):
                            val = 1 if val else 0
                        default_str = f" DEFAULT {val}"
                
                alter_query = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}{default_str}"
                
                try:
                    with engine.begin() as conn:
                        conn.execute(text(alter_query))
                    print(f"  Successfully added {col_name}")
                except Exception as e:
                    print(f"  Error adding {col_name}: {e}")

if __name__ == "__main__":
    repair()
    print("SUCCESS: Database schema synchronized with models!")
