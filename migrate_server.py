# migrate_server.py
from app import create_app, db
from sqlalchemy import text

app = create_app()


def run_migration():
    with app.app_context():
        print("⚙️ Starting Comprehensive Database Migration...")

        # List of potentially missing columns to check/add
        # Format: (Table Name, Column Name, SQL Type)
        columns_to_patch = [
            ("user", "email", "VARCHAR(150)"),
            ("task", "created_date", "DATETIME"),
            ("task", "last_completed", "DATETIME"),
            ("task", "is_habit", "BOOLEAN"),
            ("task", "recurrence", "VARCHAR(20)"),
            ("task", "color", "VARCHAR(20)"),
            ("task", "category", "VARCHAR(50)")
        ]

        with db.engine.connect() as conn:
            for table, col, col_type in columns_to_patch:
                try:
                    print(f"   👉 Checking '{table}.{col}'...")
                    # Try to add the column
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    conn.commit()
                    print(f"      ✅ SUCCESS: Added '{col}' column.")
                except Exception as e:
                    # If it fails because the column exists, that is GOOD.
                    if "duplicate column" in str(e).lower() or "exists" in str(e).lower():
                        print(f"      👌 OK: Column '{col}' already exists.")
                    else:
                        print(f"      ⚠️ Warning: Issue with '{col}': {e}")

        print("🏁 Migration Complete. Your database is now synced.")


if __name__ == '__main__':
    run_migration()
