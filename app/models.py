from app.extensions import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    # 👇 THIS LINE WAS MISSING. Add it to fix the login crash.
    email = db.Column(db.String(150), unique=True, nullable=True)
    password = db.Column(db.String(150), nullable=False)

    # Relationships
    tasks = db.relationship('Task', backref='user', lazy=True)
    habits = db.relationship('TaskHistory', backref='user', lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(20), default='normal')
    category = db.Column(db.String(50), default='general')
    complete = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime(timezone=True), default=func.now())
    due_date = db.Column(db.DateTime(timezone=True), nullable=True)
    last_completed = db.Column(db.DateTime(timezone=True), nullable=True)

    # Visuals
    color = db.Column(db.String(20), default='#3b5bdb')
    recurrence = db.Column(db.String(20), default='none')
    is_habit = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    completed_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='completed')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
