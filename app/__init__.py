"""Flask application factory."""

import os


def create_app(config_name=None):
    """Create and configure the Flask application."""
    # Import Flask only when creating the app
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)

    # Load configuration
    from .config import config
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    # Initialize extensions
    CORS(app)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from .api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register main routes
    from .api.routes import main_bp
    app.register_blueprint(main_bp)

    return app
