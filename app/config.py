"""Flask application configuration."""

import os
from pathlib import Path


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'docx'}

    # Firebase configuration
    FIREBASE_CREDENTIALS = os.environ.get('FIREBASE_CREDENTIALS', 'firebase-service-account.json')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', '')

    # Firebase Web Config (for frontend) - set these from your Firebase Console
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', '')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN', '')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', '')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID', '')

    # Redis configuration (optional for task queue)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Playwright configuration
    PLAYWRIGHT_HEADLESS = os.environ.get('PLAYWRIGHT_HEADLESS', 'false').lower() == 'true'
    BROWSER_STATE_PATH = os.environ.get('BROWSER_STATE_PATH', 'browser_state')

    # SciENcv configuration
    SCIENCV_URL = os.environ.get('SCIENCV_URL', 'https://www.ncbi.nlm.nih.gov/labs/sciencv/')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = 'production'
    # In production, Firebase credentials come from environment or default credentials


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    UPLOAD_FOLDER = 'test_uploads'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
