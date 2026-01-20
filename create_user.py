from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Check if user exists
    if not User.query.filter_by(username='jorg').first():
        user = User(username='jorg')
        user.set_password('2323')  # Set your password here
        db.session.add(user)
        db.session.commit()
        print("User 'jorg' created!")
    else:
        print("User already exists.")
