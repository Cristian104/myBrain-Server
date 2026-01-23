import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'

    # 1. Construct the absolute path
    # 'app.instance_path' is automatically set by Flask to /app/instance
    db_path = os.path.join(app.instance_path, 'db.sqlite')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # 2. AUTO-CREATE THE FOLDER (Crucial Step)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass  # Folder already exists, ignore error

    db.init_app(app)

    # Initialize Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # --- User Loader ---
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    # -------------------

    # Start Bot Listener (Safety Switch)
    if os.environ.get('ENABLE_BOT') == 'true':
        if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            from .telegram_bot import start_bot_listener
            start_bot_listener(app)

    # Register Blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
