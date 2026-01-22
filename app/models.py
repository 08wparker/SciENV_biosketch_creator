"""Database models for user authentication and biosketch persistence."""

from __future__ import annotations
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to saved biosketches
    biosketches = db.relationship('SavedBiosketch', backref='user', lazy='dynamic',
                                   cascade='all, delete-orphan')

    def set_password(self, password: str):
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if password matches."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class SavedBiosketch(db.Model):
    """Saved biosketch data for a user."""
    __tablename__ = 'saved_biosketches'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200))  # Biosketch name/label
    data = db.Column(db.JSON, nullable=False)  # Full biosketch JSON data
    selected_contributions = db.Column(db.JSON)  # Indices of selected contributions
    selected_products = db.Column(db.JSON)  # Indices of selected products
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SavedBiosketch {self.job_id} for user {self.user_id}>'
