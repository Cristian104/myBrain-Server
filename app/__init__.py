import os
from flask import Flask
# 👇 CHANGE 1: Import shared tools from extensions
from app.extensions import db, login_manager


def create_app():
    app = Flask(__name__)

    # Secret Key
    app.config['SECRET_KEY'] = 'f28df1df3969656a76704e28b9dbaa75e93dabc80853267c8e6c0e9ddd6c415a'

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
    # 👇 CHANGE 2: Absolute import
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- REGISTER BLUEPRINTS (THE NEW WIRING) ---

    # 👇 CHANGE 3: Registering the new modules

    # 1. Auth Module
    from app.modules.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    # 2. Dashboard Module
    from app.modules.dashboard.routes import dashboard_bp
    app.register_blueprint(dashboard_bp)

    # --------------------------------------------

    # Start Bot Listener
    if os.environ.get('ENABLE_BOT') == 'true':
        if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            from app.telegram_bot import start_bot_listener
            start_bot_listener(app)

    # Start Scheduler
    # 👇 CHANGE 4: Absolute import
    from app.scheduler import start_scheduler
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_scheduler(app)

    return app
