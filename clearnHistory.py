import sqlite3
import os

db_path = os.path.join('instance', 'db.sqlite')

print("🧹 Cleaning up ghost history...")

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    # Delete any history record where the task_id no longer exists in the task table
    cursor.execute("""
        DELETE FROM task_history 
        WHERE task_id NOT IN (SELECT id FROM task)
    """)

    rows = cursor.rowcount
    conn.commit()

print(f"✅ Deleted {rows} orphan history logs.")
print("🚀 Restart your server and the fake dots will be gone!")
