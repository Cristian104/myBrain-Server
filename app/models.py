from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))

    # Relationship: One user has many tasks
    tasks = db.relationship('Task', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# NEW: The Task Model


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    complete = db.Column(db.Boolean, default=False)

    # NEW FIELDS
    # normal, high, urgent
    priority = db.Column(db.String(20), default='normal')
    due_date = db.Column(db.DateTime, nullable=True)      # Target date
    # Hex color (e.g., #ff0000)
    color = db.Column(db.String(7), default='#3b5bdb')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
