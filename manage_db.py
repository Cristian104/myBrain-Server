import sqlite3
import json
import os
import sys
from app import create_app, db
# Import ALL models to ensure SQLAlchemy creates them
from app.models import User, Task
from app.modules.gym.models import GymRoutine, GymExercise, GymLog, GymProgram, GymExerciseLibrary

# Configuration
DB_FILE = os.path.join('instance', 'db.sqlite')
BACKUP_FILE = 'full_backup.json'

# Statistics for the final report
STATS = {
    "tables_found": [],
    "backup_counts": {},
    "tables_created": [],
    "restored_counts": {},
    "skipped_tables": []
}


def get_db_tables(cursor):
    """Returns a list of all table names in the database."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
    return [row['name'] for row in cursor.fetchall()]


def backup_database():
    """Backs up data to JSON and records statistics."""
    if not os.path.exists(DB_FILE):
        print(f"⚠️  No database found at {DB_FILE}. Starting fresh.")
        return None

    print(f"📦 Backing up data from {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    backup_data = {}
    tables = get_db_tables(cursor)
    STATS["tables_found"] = tables

    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = [dict(row) for row in cursor.fetchall()]
            backup_data[table] = rows
            STATS["backup_counts"][table] = len(rows)
            print(f"   - {table}: {len(rows)} rows backed up.")
        except Exception as e:
            print(f"   ❌ Error backing up {table}: {e}")

    conn.close()

    with open(BACKUP_FILE, 'w') as f:
        json.dump(backup_data, f, indent=4, default=str)

    return backup_data


def recreate_database():
    """Deletes DB file and creates fresh tables from SQLAlchemy models."""
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print(f"💥 Old database deleted.")
        except PermissionError:
            print("❌ Error: Database is locked! Stop the server first.")
            return False

    print("🏗️  Building new database schema...")
    app = create_app()
    with app.app_context():
        db.create_all()

        # Verify creation
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            STATS["tables_created"] = get_db_tables(cursor)

    return True


def restore_data():
    """Restores data and handles schema mismatches."""
    if not os.path.exists(BACKUP_FILE):
        return

    print("♻️  Restoring data...")
    with open(BACKUP_FILE, 'r') as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get schema of the NEW database
    new_db_schema = {}
    for table in STATS["tables_created"]:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        new_db_schema[table] = columns

    for table, rows in data.items():
        if table not in new_db_schema:
            STATS["skipped_tables"].append(table)
            continue

        valid_columns = new_db_schema[table]
        success_count = 0

        for row in rows:
            # Only keep columns that exist in the new schema (Handle dropped columns)
            filtered_row = {k: v for k, v in row.items() if k in valid_columns}

            # If new columns were added in code, they will rely on SQL default values here

            keys = ', '.join(filtered_row.keys())
            placeholders = ', '.join(['?'] * len(filtered_row))
            values = list(filtered_row.values())

            sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
            try:
                cursor.execute(sql, values)
                success_count += 1
            except Exception as e:
                pass  # Fail silently on individual row errors, or print if needed

        STATS["restored_counts"][table] = success_count

    conn.commit()
    conn.close()


def print_summary():
    """Prints a pretty report of the operation."""
    print("\n" + "="*60)
    print("📢  MIGRATION REPORT")
    print("="*60)

    print(f"{'TABLE NAME':<30} | {'OLD (Backup)':<12} | {'NEW (Restored)':<12} | {'STATUS'}")
    print("-" * 75)

    all_tables = set(STATS["tables_found"] + STATS["tables_created"])

    for table in sorted(all_tables):
        old_count = STATS["backup_counts"].get(table, 0)
        new_count = STATS["restored_counts"].get(table, 0)

        status = "✅ OK"
        if table in STATS["skipped_tables"]:
            status = "⚠️  DROPPED"
        elif table not in STATS["backup_counts"]:
            status = "✨ NEW TABLE"
        elif new_count < old_count:
            diff = old_count - new_count
            status = f"🔻 LOSS (-{diff})"

        print(f"{table:<30} | {old_count:<12} | {new_count:<12} | {status}")

    print("-" * 75)
    print("NOTE: 'DROPPED' means the table no longer exists in your code.")
    print("NOTE: 'LOSS' might happen if new constraints (like Unique) rejected old duplicates.")
    print("="*60 + "\n")


def main():
    if backup_database() is None:
        if input("Create new DB anyway? (y/n): ").lower() != 'y':
            return

    if recreate_database():
        restore_data()
        print_summary()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "backup":
        print("📦 Backup mode activated — dumping data only...")
        backup_database()
        print("✅ JSON backup completed: full_backup.json")
        sys.exit(0)  # Exit cleanly — no recreate/restore
    else:
        print("🔄 Full migration mode...")
        backup_data = backup_database()
        if backup_data is None:
            if input("Create new DB anyway? (y/n): ").lower() != 'y':
                sys.exit(0)

        if recreate_database():
            restore_data()
            print_summary()
