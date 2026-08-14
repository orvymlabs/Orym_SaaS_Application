# Production Database Setup & Troubleshooting

If you are seeing "Internal Server Error: (sqlite3.OperationalError) no such table: ..." in production, follow these steps to fix the issue.

## 1. Why this happens
This error occurs when the backend cannot find the required database tables. In production (Render), this is usually due to one of two reasons:
1.  **Missing Database Connection:** The app is falling back to an in-memory SQLite database because it cannot connect to your PostgreSQL database.
2.  **Initialization Failure:** The automatic table creation failed during startup.
3.  **Ephemeral Storage:** You are using SQLite but haven't attached a Persistent Disk on Render, so the database file is deleted every time the app restarts.

## 2. Recommended Fix: Use PostgreSQL
For production, you should use a PostgreSQL database. 
1.  Create a PostgreSQL instance on Render.
2.  Add an environment variable to your Web Service:
    -   Key: `POSTGRES_URL`
    -   Value: Your PostgreSQL External Connection String (e.g., `postgres://user:pass@host:port/db`)
3.  Restart the service.

## 3. If using SQLite
If you must use SQLite:
1.  Go to Render Dashboard -> Your Service -> **Settings**.
2.  Scroll to **Disks** and add a Disk.
    -   Name: `data`
    -   Mount Path: `/opt/render/project/src/backend/data` (or wherever your `backend/data` is located)
3.  Ensure your `DATABASE_URL` points to this persistent path.

## 4. Run Diagnostics
I have added a diagnostic script to help you. You can run it from the Render Shell:

```bash
cd backend
python diagnose_db.py
```

This script will:
-   Check if it can connect to the database.
-   List existing tables.
-   Attempt to create missing tables if any are found.

## 5. Manual Table Creation
If the tables are still missing, you can force creation by running:

```bash
cd backend
python -c "from database import init_db; init_db()"
```

## 6. Verify Logs
Check your Render Logs for any lines starting with `CRITICAL: DATABASE INITIALIZATION FAILED`. These logs will contain the specific error message explaining why the database could not be set up.
