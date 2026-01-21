import sqlite3
import os
from werkzeug.security import generate_password_hash

# --- CONFIGURATION ---
TARGET_USERNAME = "jorg"  # The username you use to log in
NEW_PASSWORD = "2323"     # The new password you want to use
# ---------------------

db_path = os.path.join('instance', 'db.sqlite')

if not os.path.exists(db_path):
    print(f"❌ Error: Database not found at {db_path}")
else:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 1. Find the user
            print(f"🔍 Looking for user '{TARGET_USERNAME}'...")
            cursor.execute(
                "SELECT id FROM user WHERE username = ?", (TARGET_USERNAME,))
            user = cursor.fetchone()

            if not user:
                print(f"❌ User '{TARGET_USERNAME}' not found!")
                print("   Existing users in DB:")
                for row in cursor.execute("SELECT username FROM user"):
                    print(f"   - {row[0]}")
            else:
                # 2. Update the password
                print(f"✅ User found (ID: {user[0]}). Resetting password...")
                hashed_pw = generate_password_hash(NEW_PASSWORD)

                cursor.execute(
                    "UPDATE user SET password = ? WHERE id = ?", (hashed_pw, user[0]))
                conn.commit()

                print("---------------------------------------------------")
                print(
                    f"🚀 SUCCESS! Password for '{TARGET_USERNAME}' is now: {NEW_PASSWORD}")
                print("---------------------------------------------------")

    except Exception as e:
        print(f"❌ Error: {e}")
