import psycopg2

url = 'postgresql://orvyn_ut1d_user:LZ7fz2r7JARnJJq4NN6pxOSy10myF4g5@dpg-d7gg8sfavr4c738p4fg0-a.ohio-postgres.render.com/orvyn_ut1d'

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    print("Checking for duplicate phone_number_ids...")
    cur.execute("SELECT phone_number_id, COUNT(*) FROM integrations WHERE phone_number_id IS NOT NULL GROUP BY phone_number_id HAVING COUNT(*) > 1")
    dupes = cur.fetchall()
    if dupes:
        print("Found duplicates:", dupes)
        print("Cleaning up duplicates (keeping the one with highest ID)...")
        for phone_id, count in dupes:
            cur.execute(f"SELECT id FROM integrations WHERE phone_number_id = '{phone_id}' ORDER BY id DESC")
            ids = [row[0] for row in cur.fetchall()]
            keep_id = ids[0]
            delete_ids = ids[1:]
            print(f"Keeping ID {keep_id}, deleting IDs {delete_ids} for phone_id {phone_id}")
            cur.execute(f"DELETE FROM integrations WHERE id IN ({','.join(map(str, delete_ids))})")
    else:
        print("No duplicates found.")

    print("Adding unique constraint to phone_number_id...")
    try:
        cur.execute("ALTER TABLE integrations ADD CONSTRAINT uq_phone_number_id UNIQUE (phone_number_id)")
        print("Unique constraint added successfully.")
    except Exception as e:
        print(f"Error adding unique constraint: {e}")
        conn.rollback()
        cur = conn.cursor()

    conn.commit()
    conn.close()
except Exception as e:
    print("Critical error:", e)
