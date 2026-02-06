from app.extensions import db
from datetime import datetime


class GymProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    routines = db.relationship(
        'GymRoutine', backref='program', lazy=True, cascade="all, delete-orphan")


class GymExerciseLibrary(db.Model):
    """Master list of exercises (Templates)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    name_es = db.Column(db.String(100))
    default_sets = db.Column(db.Integer, default=3)
    default_reps = db.Column(db.String(20), default="8-12")

    # NEW MEDIA COLUMNS
    video_url = db.Column(db.String(255))  # YouTube Link
    image_filename = db.Column(db.String(255))  # Local GIF/Image file

    __table_args__ = (db.UniqueConstraint(
        'user_id', 'name_en', name='_user_exercise_uc'),)


class GymRoutine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey(
        'gym_program.id'), nullable=True)
    name = db.Column(db.String(50), nullable=False)
    order_index = db.Column(db.Integer)
    notes = db.Column(db.String(200))
    exercises = db.relationship(
        'GymExercise', backref='routine', lazy=True, cascade="all, delete-orphan")


class GymExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    routine_id = db.Column(db.Integer, db.ForeignKey(
        'gym_routine.id'), nullable=False)
    library_id = db.Column(db.Integer, db.ForeignKey(
        'gym_exercise_library.id'), nullable=True)

    # Allow access to the parent library item to fetch the GIF/Video dynamically
    library_item = db.relationship('GymExerciseLibrary', backref='instances')

    name = db.Column(db.String(100), nullable=False)
    name_es_display = db.Column(db.String(100))
    target_sets = db.Column(db.Integer, default=3)
    target_reps = db.Column(db.String(20))
    logs = db.relationship('GymLog', backref='exercise', lazy=True)


class GymLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey(
        'gym_exercise.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    weight_used = db.Column(db.Float)
    reps_done = db.Column(db.Integer)
    is_personal_record = db.Column(db.Boolean, default=False)
