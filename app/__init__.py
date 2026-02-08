import os
from flask import Flask

# Extensions & Models (import early for init)
from app.extensions import db, login_manager
from app.models import User

# Blueprints (import after app creation to avoid circular issues)
from app.modules.auth.routes import auth_bp
from app.modules.dashboard.routes import dashboard_bp
from app.modules.gym.routes import gym_bp
from app.modules.tasks.routes import tasks_bp  # ← NEW: Tasks/Reminders module


def create_app():
    app = Flask(__name__)

    # --- SECURE CONFIG FROM .ENV ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        raise ValueError("❌ SECRET_KEY must be set in .env!")

    # Database Config
    db_path = os.path.join(app.instance_path, 'db.sqlite')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # Auto-create instance folder
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # User Loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- REGISTER BLUEPRINTS ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(gym_bp)         # Your gym tracker module
    app.register_blueprint(tasks_bp)       # ← NEW: Separate reminders/to-do module

    # Start Bot Listener (only in prod or proper debug)
    if os.getenv('ENABLE_BOT') == 'true':
        if not app.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
            from app.telegram_bot import start_bot_listener
            start_bot_listener(app)

    # Start Scheduler
    from app.scheduler import start_scheduler
    if not app.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
        start_scheduler(app)

    return app