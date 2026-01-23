"""Authentication routes for Firebase Auth.

Authentication is handled client-side with Firebase JS SDK.
Server-side routes verify tokens and provide profile data.
"""

from __future__ import annotations
from flask import Blueprint, request, render_template, redirect, url_for, jsonify, g

from ..firebase_config import firebase_auth_required, get_user_info
from ..firestore_models import get_user_biosketches

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login():
    """Render the login page.

    Actual authentication is handled client-side with Firebase JS SDK.
    """
    return render_template('auth/login.html')


@auth_bp.route('/register')
def register():
    """Render the registration page.

    Actual registration is handled client-side with Firebase JS SDK.
    """
    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    """Render logout page.

    Actual logout is handled client-side with Firebase JS SDK.
    """
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
def profile():
    """Render the profile page.

    User data and biosketches are loaded client-side via API calls.
    """
    return render_template('auth/profile.html')


# ============ API Endpoints for Firebase Auth ============

@auth_bp.route('/api/me')
@firebase_auth_required
def get_current_user():
    """Get current user info from Firebase Auth.

    Requires valid Firebase ID token in Authorization header.
    """
    user_info = get_user_info(g.user_id)
    if not user_info:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user_info)


@auth_bp.route('/api/biosketches')
@firebase_auth_required
def get_my_biosketches():
    """Get all biosketches for the authenticated user.

    Requires valid Firebase ID token in Authorization header.
    """
    biosketches = get_user_biosketches(g.user_id)

    # Convert timestamps to ISO format for JSON serialization
    for bs in biosketches:
        if bs.get('created_at'):
            bs['created_at'] = bs['created_at'].isoformat() if hasattr(bs['created_at'], 'isoformat') else str(bs['created_at'])
        if bs.get('updated_at'):
            bs['updated_at'] = bs['updated_at'].isoformat() if hasattr(bs['updated_at'], 'isoformat') else str(bs['updated_at'])

    return jsonify(biosketches)


@auth_bp.route('/api/verify-token', methods=['POST'])
@firebase_auth_required
def verify_token():
    """Verify a Firebase ID token.

    Useful for checking if a token is still valid.
    """
    return jsonify({
        'valid': True,
        'uid': g.user_id,
        'email': g.firebase_user.get('email')
    })
