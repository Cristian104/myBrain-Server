import sys
from app import create_app, db
from app.models import User
import getpass

app = create_app()


def reset_db():
    """Wipes the database and starts fresh."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✅ Database reset complete.")


def create_admin():
    """Creates the main admin user."""
    with app.app_context():
        print("\n--- SETUP ADMIN USER ---")
        username = input("Enter Admin Username (default: admin): ") or 'admin'

        # getpass hides what you type so it doesn't show on screen
        password = getpass.getpass("Enter New Secure Password: ")
        confirm = getpass.getpass("Confirm Password: ")

        if password != confirm:
            print("❌ Passwords do not match!")
            return

        # Check if user exists
        if User.query.filter_by(username=username).first():
            print(f"ℹ️ User {username} already exists.")
            return

        new_user = User(username=username, role='admin')
        new_user.set_password(password)  # This hashes it automatically!

        db.session.add(new_user)
        db.session.commit()
        print(f"✅ User '{username}' created successfully!")


if __name__ == '__main__':
    # Simple CLI menu
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_db()
        create_admin()
    else:
        create_admin()
