from app import create_app, db
from app.models import User, Task

app = create_app()

with app.app_context():
    # 1. Create all tables (User, Task) with the latest schema
    db.create_all()
    print("✅ Database tables created successfully.")

    # 2. Create the Admin User
    if not User.query.filter_by(username='jorg').first():
        user = User(username='jorg')
        user.set_password('2323')  # Hashes '2323' securely
        db.session.add(user)
        db.session.commit()
        print("👤 User 'jorg' created with password '2323'.")
    else:
        print("ℹ️ User 'jorg' already exists.")
