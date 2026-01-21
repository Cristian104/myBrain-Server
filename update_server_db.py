import sqlite3
import os
from werkzeug.security import generate_password_hash

# --- CONFIGURATION ---
TARGET_USER = "jorg"
TARGET_PASS = "2323"
# ---------------------

db_path = os.path.join('instance', 'db.sqlite')


def patch_database():
    if not os.path.exists(db_path):
        print(f"❌ Error: Database not found at {db_path}")
        return

    print(f"🔧 Connecting to database: {db_path}...")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 1. CREATE TASK_HISTORY TABLE (If missing)
            print("Checking for 'task_history' table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY,
                    task_id INTEGER NOT NULL,
                    completed_date DATE NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES task(id)
                )
            ''')

            # 2. UPDATE USER TABLE (Add Password)
            print("Checking 'user' table columns...")
            cursor.execute("PRAGMA table_info(user)")
            user_cols = [info[1] for info in cursor.fetchall()]

            if 'password' not in user_cols:
                print("⚠️ Adding missing 'password' column...")
                # Add column with a temporary default
                cursor.execute(
                    f"ALTER TABLE user ADD COLUMN password TEXT DEFAULT 'temp_hash'")

            # 3. FORCE PASSWORD FOR 'JORG'
            # This ensures your existing user works immediately with 2323
            print(
                f"🔐 Setting password for '{TARGET_USER}' to '{TARGET_PASS}'...")
            hashed_pw = generate_password_hash(TARGET_PASS)
            cursor.execute(
                "UPDATE user SET password = ? WHERE username = ?", (hashed_pw, TARGET_USER))

            # 4. UPDATE TASK TABLE (Add Habits, Categories, etc)
            print("Checking 'task' table columns...")
            cursor.execute("PRAGMA table_info(task)")
            task_cols = [info[1] for info in cursor.fetchall()]

            new_columns = {
                'recurrence': "TEXT DEFAULT 'none'",
                'category': "TEXT DEFAULT 'general'",
                'is_habit': "BOOLEAN DEFAULT 0",
                'last_completed': "DATETIME",
                'color': "TEXT DEFAULT '#3b5bdb'"
            }

            for col_name, col_def in new_columns.items():
                if col_name not in task_cols:
                    print(f"⚠️ Adding missing '{col_name}' column...")
                    cursor.execute(
                        f"ALTER TABLE task ADD COLUMN {col_name} {col_def}")

            conn.commit()
            print("\n🚀 DATABASE UPDATE COMPLETE! Server is ready.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")


if __name__ == "__main__":
    patch_database()
