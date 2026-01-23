"""Firebase Admin SDK initialization and authentication helpers."""

from __future__ import annotations
import os
from functools import wraps
from flask import request, jsonify, g
import firebase_admin
from firebase_admin import auth, credentials, firestore

# Global Firestore client
_db = None


def init_firebase(app):
    """Initialize Firebase Admin SDK and return Firestore client."""
    global _db

    # Check if already initialized
    if firebase_admin._apps:
        _db = firestore.client()
        return _db

    # Get credentials path from config or environment
    cred_path = app.config.get('FIREBASE_CREDENTIALS') or os.environ.get('FIREBASE_CREDENTIALS')

    if cred_path and os.path.exists(cred_path):
        # Use service account file
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        # Use Application Default Credentials (for Cloud Run)
        firebase_admin.initialize_app()

    _db = firestore.client()
    return _db


def get_firestore_client():
    """Get the Firestore client instance."""
    global _db
    if _db is None:
        _db = firestore.client()
    return _db


def firebase_auth_required(f):
    """Decorator to require Firebase authentication.

    Verifies the Firebase ID token from Authorization header.
    Sets g.firebase_user with the decoded token data.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401

        token = auth_header.replace('Bearer ', '')

        try:
            decoded_token = auth.verify_id_token(token)
            g.firebase_user = decoded_token
            g.user_id = decoded_token['uid']
        except auth.InvalidIdTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except auth.ExpiredIdTokenError:
            return jsonify({'error': 'Token expired'}), 401
        except Exception as e:
            return jsonify({'error': f'Authentication failed: {str(e)}'}), 401

        return f(*args, **kwargs)
    return decorated


def firebase_auth_optional(f):
    """Decorator for optional Firebase authentication.

    If a valid token is provided, sets g.firebase_user and g.user_id.
    If no token or invalid token, g.firebase_user and g.user_id are None.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        g.firebase_user = None
        g.user_id = None

        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            try:
                decoded_token = auth.verify_id_token(token)
                g.firebase_user = decoded_token
                g.user_id = decoded_token['uid']
            except Exception:
                # Invalid token, but authentication is optional
                pass

        return f(*args, **kwargs)
    return decorated


def get_user_info(uid: str) -> dict:
    """Get user info from Firebase Auth."""
    try:
        user = auth.get_user(uid)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'photo_url': user.photo_url
        }
    except Exception:
        return None
