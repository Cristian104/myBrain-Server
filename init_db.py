# init_db.py
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os

app = create_app()


def reset_database():
    with app.app_context():
        # 1. Define the DB path
        db_path = os.path.join(app.instance_path, 'db.sqlite')

        # 2. Delete existing DB if it exists (Hard Reset)
        if os.path.exists(db_path):
            print(f"🗑️ Deleting old database at {db_path}...")
            os.remove(db_path)
        else:
            print("✨ No existing database found. Starting fresh.")

        # 3. Create Tables
        print("🔨 Creating new database tables...")
        db.create_all()

        # 4. Create Admin User
        print("👤 Creating Admin User...")

        USERNAME = "jorg"
        EMAIL = "jorg@mybrain.com"  # This is crucial for your auth.py logic
        PASSWORD = "2323"

        new_user = User(
            username=USERNAME,
            email=EMAIL,
            password=generate_password_hash(PASSWORD, method='pbkdf2:sha256')
        )

        db.session.add(new_user)
        db.session.commit()

        print("✅ Database initialized successfully!")
        print(f"👉 Login with: {USERNAME} / {PASSWORD}")


if __name__ == '__main__':
    reset_database()
