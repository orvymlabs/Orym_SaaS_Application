"""
Migration script: SQLite -> Neon PostgreSQL (v2)
Handles: boolean type conversion, column alignment, foreign key order, transaction recovery
"""
import sqlite3
import psycopg2
import os

NEON_URL = "postgresql://neondb_owner:npg_W3aiHOuL9Skl@ep-lively-frost-ayvbiky3-pooler.c-5.us-east-2.aws.neon.tech/neondb"
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "data", "saas_bot.db")
BACKUP_PATH = os.path.join(os.path.dirname(__file__), "data", "saas_bot_backup_20260514_203928.db")

TABLES_ORDER = [
    "plans",
    "users",
    "subscriptions",
    "bots",
    "bot_settings",
    "integrations",
    "usage_stats",
    "messages",
    "leads",
    "site_info_cache",
    "announcements",
    "orders",
    "user_templates",
    "notifications",
    "audit_logs",
    "system_settings",
]

BOOLEAN_COLUMNS = {
    "orders", "bots", "bot_settings", "integrations", "messages",
    "announcements", "notifications", "leads", "subscriptions",
    "usage_stats", "site_info_cache", "plans",
}

def get_pg_columns(pg_cur, table):
    pg_cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = %s ORDER BY ordinal_position", (table,)
    )
    return {row[0]: row[1] for row in pg_cur.fetchall()}

def get_sqlite_columns(sl_cur, table):
    sl_cur.execute(f"PRAGMA table_info('{table}')")
    return [(row[1], row[2]) for row in sl_cur.fetchall()]

def clean_value(val, pg_type):
    if val is None:
        return None
    if isinstance(val, bytes):
        return None
    if pg_type == "boolean":
        return bool(val)
    if pg_type == "integer" and isinstance(val, str):
        try:
            return int(val)
        except:
            return 0
    return val

def migrate_table(sl_cur, pg_cur, pg_conn, table):
    sl_cols_info = get_sqlite_columns(sl_cur, table)
    pg_cols = get_pg_columns(pg_cur, table)

    common_cols = []
    for sl_col_name, sl_col_type in sl_cols_info:
        if sl_col_name in pg_cols:
            common_cols.append((sl_col_name, pg_cols[sl_col_name]))

    if not common_cols:
        return 0

    col_names_str = ", ".join([f'"{c[0]}"' for c in common_cols])
    placeholders = ", ".join(["%s"] * len(common_cols))
    insert_sql = f'INSERT INTO "{table}" ({col_names_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

    sl_col_names = [c[0] for c in common_cols]
    sl_cur.execute(f"SELECT {', '.join(['\"' + c + '\"' for c in [x[0] for x in sl_cols_info]])} FROM \"{table}\"")
    rows = sl_cur.fetchall()

    if not rows:
        return 0

    sl_col_map = {c[0]: i for i, c in enumerate(sl_cols_info)}
    inserted = 0

    for row in rows:
        cleaned = []
        for col_name, pg_type in common_cols:
            idx = sl_col_map[col_name]
            val = row[idx] if idx < len(row) else None
            cleaned.append(clean_value(val, pg_type))
        try:
            pg_cur.execute(insert_sql, cleaned)
            inserted += pg_cur.rowcount
        except Exception as e:
            pg_conn.rollback()
            if "unique" not in str(e).lower() and "duplicate" not in str(e).lower():
                print(f"    WARN: {e}")

    pg_conn.commit()
    return inserted


def main():
    print("=== SQLite -> Neon PostgreSQL Migration (v2) ===\n")

    pg_conn = psycopg2.connect(NEON_URL, sslmode="require", connect_timeout=15)
    pg_cur = pg_conn.cursor()

    # Clear existing data (except plans which we'll re-seed)
    print("--- Clearing existing data ---")
    for table in reversed(TABLES_ORDER):
        try:
            pg_cur.execute(f'DELETE FROM "{table}"')
            pg_conn.commit()
        except:
            pg_conn.rollback()
    print("  Cleared.\n")

    # Phase 1: Migrate from main data/saas_bot.db
    print("--- Phase 1: data/saas_bot.db ---")
    sl_conn = sqlite3.connect(SQLITE_PATH)
    sl_cur = sl_conn.cursor()

    for table in TABLES_ORDER:
        try:
            count = migrate_table(sl_cur, pg_cur, pg_conn, table)
            print(f"  {table}: {count} rows")
        except Exception as e:
            pg_conn.rollback()
            print(f"  {table}: ERROR - {e}")

    sl_conn.close()

    # Phase 2: Merge backup data for missing tables/rows
    if os.path.exists(BACKUP_PATH):
        print("\n--- Phase 2: backup db (users, bots, etc.) ---")
        bk_conn = sqlite3.connect(BACKUP_PATH)
        bk_cur = bk_conn.cursor()

        # Get existing user IDs from PG
        pg_cur.execute('SELECT id FROM users')
        existing_user_ids = {r[0] for r in pg_cur.fetchall()}

        # Get existing bot IDs from PG
        pg_cur.execute('SELECT id FROM bots')
        existing_bot_ids = {r[0] for r in pg_cur.fetchall()}

        # Insert extra users from backup
        sl_cols_info = get_sqlite_columns(bk_cur, "users")
        sl_cur_map = {c[0]: i for i, c in enumerate(sl_cols_info)}
        bk_cur.execute("SELECT * FROM users")
        extra_users = 0
        for row in bk_cur.fetchall():
            uid = row[sl_cur_map["id"]]
            if uid not in existing_user_ids:
                email = row[sl_cur_map["email"]]
                role = row[sl_cur_map["role"]]
                plan = row[sl_cur_map["plan"]]
                ph = row[sl_cur_map["password_hash"]] if "password_hash" in sl_cur_map else None
                fn = row[sl_cur_map["full_name"]] if "full_name" in sl_cur_map else None
                ca = row[sl_cur_map["created_at"]] if "created_at" in sl_cur_map else None
                try:
                    pg_cur.execute(
                        'INSERT INTO "users" (id, email, role, plan, password_hash, full_name, created_at) '
                        'VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                        (uid, email, role, plan, ph, fn, ca)
                    )
                    extra_users += pg_cur.rowcount
                    existing_user_ids.add(uid)
                except Exception as e:
                    pg_conn.rollback()
        pg_conn.commit()
        print(f"  users: +{extra_users} from backup")

        # Insert extra bots from backup
        sl_cols_info = get_sqlite_columns(bk_cur, "bots")
        sl_cur_map = {c[0]: i for i, c in enumerate(sl_cols_info)}
        bk_cur.execute("SELECT * FROM bots")
        extra_bots = 0
        for row in bk_cur.fetchall():
            bid = row[sl_cur_map["id"]]
            if bid not in existing_bot_ids and row[sl_cur_map["user_id"]] in existing_user_ids:
                uid = row[sl_cur_map["user_id"]]
                mode = row[sl_cur_map["mode"]]
                status = bool(row[sl_cur_map["status"]])
                ca = row[sl_cur_map["created_at"]] if "created_at" in sl_cur_map else None
                try:
                    pg_cur.execute(
                        'INSERT INTO "bots" (id, user_id, mode, status, created_at) '
                        'VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                        (bid, uid, mode, status, ca)
                    )
                    extra_bots += pg_cur.rowcount
                    existing_bot_ids.add(bid)
                except Exception as e:
                    pg_conn.rollback()
        pg_conn.commit()
        print(f"  bots: +{extra_bots} from backup")

        # Migrate all other tables from backup
        for table in TABLES_ORDER:
            if table in ("plans", "users", "bots"):
                continue
            try:
                count = migrate_table(bk_cur, pg_cur, pg_conn, table)
                if count > 0:
                    print(f"  {table}: +{count} from backup")
            except:
                pg_conn.rollback()

        bk_conn.close()

    # Final verification
    print("\n--- Final Verification ---")
    total = 0
    for table in TABLES_ORDER:
        try:
            pg_cur.execute(f'SELECT count(*) FROM "{table}"')
            count = pg_cur.fetchone()[0]
            total += count
            print(f"  {table}: {count} rows")
        except:
            pass
    print(f"\n  Total rows: {total}")

    pg_conn.close()
    print("\n=== Migration Complete ===")


if __name__ == "__main__":
    main()
