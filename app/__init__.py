"""Flask application factory."""

import os


def create_app(config_name=None):
    """Create and configure the Flask application."""
    # Import Flask only when creating the app
    from flask import Flask
    from flask_cors import CORS
    from flask_login import LoginManager

    app = Flask(__name__)

    # Load configuration
    from .config import config
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    # Initialize extensions
    CORS(app)

    # Initialize database
    from .models import db
    db.init_app(app)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # Create database tables
    with app.app_context():
        db.create_all()

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from .api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register main routes
    from .api.routes import main_bp
    app.register_blueprint(main_bp)

    # Register auth routes
    from .api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
