import sqlite3
import os

# Path to your database
db_path = os.path.join('instance', 'db.sqlite')

# The SQL commands we need to run
commands = [
    # 1. Add 'is_habit' column
    "ALTER TABLE task ADD COLUMN is_habit BOOLEAN DEFAULT 0;",

    # 2. Add 'last_completed' column
    "ALTER TABLE task ADD COLUMN last_completed TIMESTAMP;",

    # 3. Create 'task_history' table
    "CREATE TABLE task_history (id INTEGER PRIMARY KEY, task_id INTEGER NOT NULL, completed_date DATE NOT NULL, FOREIGN KEY(task_id) REFERENCES task(id));"
]

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
else:
    print(f"Connecting to database: {db_path}...")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for cmd in commands:
                try:
                    cursor.execute(cmd)
                    print(f"✅ Success: {cmd}")
                except sqlite3.OperationalError as e:
                    # If column already exists, this error pops up. It's safe to ignore.
                    print(
                        f"⚠️ Skipped (may already exist): {cmd} \n   Reason: {e}")
            conn.commit()
        print("\n🚀 Migration Complete! Your database is ready for Phase 3.")
    except Exception as e:
        print(f"❌ Critical Error: {e}")
