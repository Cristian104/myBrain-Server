# migrate_server.py
from app import create_app, db
from sqlalchemy import text
import os

app = create_app()


def run_migration():
    with app.app_context():
        print("⚙️ Checking database...")

        try:
            # 1. Connect to the database directly
            with db.engine.connect() as conn:
                # 2. Attempt to add the missing column
                # SQLite syntax: ALTER TABLE {table} ADD COLUMN {name} {type}
                conn.execute(
                    text("ALTER TABLE user ADD COLUMN email VARCHAR(150)"))
                conn.commit()

            print("✅ SUCCESS: 'email' column added to 'user' table.")

        except Exception as e:
            # If it fails, it usually means the column already exists
            if "duplicate column" in str(e).lower() or "exists" in str(e).lower():
                print("ℹ️ Info: The 'email' column already exists. No changes made.")
            else:
                print(f"❌ Error during migration: {e}")


if __name__ == '__main__':
    run_migration()
