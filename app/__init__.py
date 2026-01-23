import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'

    # ✅ FIX: Point to the 'instance' folder so Docker saves it!
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/db.sqlite'

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
