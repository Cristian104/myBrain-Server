import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)

    # Initialize Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # --- FIX START: Add the User Loader ---
    from .models import User  # Import inside to avoid circular import

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    # --- FIX END --------------------------

    # Start Bot Listener (Only if not in debug reload)
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        from .telegram_bot import start_bot_listener
        start_bot_listener(app)

    # Register Blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
