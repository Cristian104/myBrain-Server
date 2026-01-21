import sqlite3
import os

db_path = os.path.join('instance', 'db.sqlite')

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
else:
    print(f"Connecting to database: {db_path}...")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 1. Check what columns currently exist
            print("Checking existing columns in 'user' table...")
            cursor.execute("PRAGMA table_info(user)")
            columns = [info[1] for info in cursor.fetchall()]
            print(f"Found columns: {columns}")

            # 2. Add 'password' column if missing
            if 'password' not in columns:
                print("⚠️ Column 'password' missing. Adding it now...")
                # We add a default value so existing users don't break
                cursor.execute(
                    "ALTER TABLE user ADD COLUMN password TEXT DEFAULT 'scrypt:32768:8:1$k7s...';")
                print("✅ Success: Added 'password' column.")
            else:
                print("✅ Column 'password' already exists.")

            conn.commit()

        print("\n🚀 User Table Fix Complete! Try running the app now.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")
