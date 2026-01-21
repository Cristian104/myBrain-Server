from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Task', backref='author', lazy=True)

    # ✅ THIS WAS MISSING
    def set_password(self, password):
        self.password = generate_password_hash(password)

    # ✅ THIS WAS CAUSING THE ERROR
    def check_password(self, password):
        return check_password_hash(self.password, password)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    complete = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='normal')
    due_date = db.Column(db.DateTime, nullable=True)
    color = db.Column(db.String(7), default='#3b5bdb')

    # Contexts & Habits (Phase 2 & 3)
    recurrence = db.Column(db.String(10), default='none')
    category = db.Column(db.String(20), default='general')
    is_habit = db.Column(db.Boolean, default=False)
    last_completed = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    # Use timezone-aware UTC now
    completed_date = db.Column(
        db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
