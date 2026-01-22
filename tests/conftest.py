"""Pytest configuration for tests."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the Flask import in app/__init__.py
# We create a minimal mock so that importing from app.parser works
class MockFlask:
    def __init__(self, *args, **kwargs):
        pass

class MockCORS:
    def __init__(self, *args, **kwargs):
        pass

# Create mock modules
import types

# Create mock flask module
flask_mock = types.ModuleType('flask')
flask_mock.Flask = MockFlask
sys.modules['flask'] = flask_mock

# Create mock flask_cors module
flask_cors_mock = types.ModuleType('flask_cors')
flask_cors_mock.CORS = MockCORS
sys.modules['flask_cors'] = flask_cors_mock
