"""Flask application factory."""

import os


def create_app(config_name=None):
    """Create and configure the Flask application."""
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)

    # Load configuration
    from .config import config
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    # Initialize extensions
    CORS(app)

    # Initialize Firebase
    from .firebase_config import init_firebase
    try:
        init_firebase(app)
    except Exception as e:
        app.logger.warning(f"Firebase initialization failed: {e}")
        app.logger.warning("App will run without Firebase - some features may be unavailable")

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from .api.routes import api_bp, main_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(main_bp)

    # Register auth routes
    from .api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Make Firebase config available to templates
    @app.context_processor
    def inject_firebase_config():
        return {
            'firebase_config': {
                'apiKey': app.config.get('FIREBASE_API_KEY', ''),
                'authDomain': app.config.get('FIREBASE_AUTH_DOMAIN', ''),
                'projectId': app.config.get('FIREBASE_PROJECT_ID', ''),
                'storageBucket': app.config.get('FIREBASE_STORAGE_BUCKET', ''),
                'messagingSenderId': app.config.get('FIREBASE_MESSAGING_SENDER_ID', ''),
                'appId': app.config.get('FIREBASE_APP_ID', '')
            }
        }

    return app
