# migrate_server.py
import os
from app import create_app, db
from sqlalchemy import text

app = create_app()


def run_migration():
    with app.app_context():
        print(f"📍 Database Path: {app.instance_path}")
        print("⚙️ Starting Database Patch...")

        # Columns to force-add
        patches = [
            ("user", "email", "VARCHAR(150)"),
            ("task", "created_date", "DATETIME"),
            ("task", "last_completed", "DATETIME"),
            ("task", "due_date", "DATETIME"),
            ("task", "is_habit", "BOOLEAN"),
            ("task", "recurrence", "VARCHAR(20)"),
            ("task", "color", "VARCHAR(20)"),
            ("task", "category", "VARCHAR(50)")
        ]

        with db.engine.connect() as conn:
            for table, col, col_type in patches:
                try:
                    # SQLite: ALTER TABLE table_name ADD COLUMN column_name column_type
                    sql = text(
                        f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                    conn.execute(sql)
                    conn.commit()
                    print(f"   ✅ Added: {table}.{col}")
                except Exception as e:
                    # If error contains "duplicate" or "exists", it's fine.
                    err = str(e).lower()
                    if "duplicate" in err or "exists" in err:
                        print(f"   👌 OK (Already exists): {table}.{col}")
                    else:
                        print(f"   ⚠️ Ignored error for {table}.{col}: {e}")

        print("🏁 Migration Finished.")


if __name__ == '__main__':
    run_migration()
