from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()
    
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='123', role='admin')
        db.session.add(admin)
        db.session.commit()
        print("✅ Database created & Admin user added!")
    else:
        print("ℹ️ Database already exists.")