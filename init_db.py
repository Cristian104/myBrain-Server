from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        # 1. Add column
        try:
            conn.execute(
                text("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
            print("✅ Column 'role' added successfully.")
        except Exception as e:
            print(f"⚠️ Column might already exist: {e}")

        # 2. Make your main user a 'dev' (Change 'jorg' to your username)
        conn.execute(
            text("UPDATE user SET role = 'dev' WHERE username = 'jorg'"))
        conn.commit()
        print("✅ User 'jorg' promoted to Developer.")
