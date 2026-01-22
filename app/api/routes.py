"""API routes for biosketch parsing and automation."""

from __future__ import annotations
import os
import uuid
import json
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from ..parser import BiosketchParser, BiosketchData


# Create blueprints
api_bp = Blueprint('api', __name__)
main_bp = Blueprint('main', __name__)

# In-memory storage for parsed data (fallback for non-logged-in users)
parsed_data_store = {}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def get_upload_path(filename: str) -> Path:
    """Get the full path for an uploaded file."""
    return Path(current_app.config['UPLOAD_FOLDER']) / filename


def get_biosketch_data(job_id: str):
    """Get biosketch data from database or memory."""
    if current_user.is_authenticated:
        from ..models import SavedBiosketch
        biosketch = SavedBiosketch.query.filter_by(job_id=job_id, user_id=current_user.id).first()
        if biosketch:
            return biosketch.data
    return parsed_data_store.get(job_id)


def save_biosketch_data(job_id: str, data: dict, selected_contributions=None, selected_products=None):
    """Save biosketch data to database or memory."""
    if current_user.is_authenticated:
        from ..models import db, SavedBiosketch
        biosketch = SavedBiosketch.query.filter_by(job_id=job_id, user_id=current_user.id).first()
        if biosketch:
            biosketch.data = data
            if selected_contributions is not None:
                biosketch.selected_contributions = selected_contributions
            if selected_products is not None:
                biosketch.selected_products = selected_products
            biosketch.name = data.get('name', 'Unnamed Biosketch')
        else:
            biosketch = SavedBiosketch(
                job_id=job_id,
                user_id=current_user.id,
                data=data,
                name=data.get('name', 'Unnamed Biosketch'),
                selected_contributions=selected_contributions,
                selected_products=selected_products
            )
            db.session.add(biosketch)
        db.session.commit()
    else:
        parsed_data_store[job_id] = data


# ============ Main Routes ============

@main_bp.route('/')
def index():
    """Render the main upload page."""
    return render_template('index.html')


@main_bp.route('/review/<job_id>')
def review(job_id: str):
    """Render the review page for parsed biosketch data."""
    data = get_biosketch_data(job_id)
    if not data:
        return render_template('error.html', message='Job not found'), 404

    # Get selected items if user is logged in
    selected_contributions = []
    selected_products = []
    if current_user.is_authenticated:
        from ..models import SavedBiosketch
        biosketch = SavedBiosketch.query.filter_by(job_id=job_id, user_id=current_user.id).first()
        if biosketch:
            selected_contributions = biosketch.selected_contributions or []
            selected_products = biosketch.selected_products or []

    return render_template('review.html',
                           job_id=job_id,
                           data=data,
                           selected_contributions=selected_contributions,
                           selected_products=selected_products)


# ============ API Routes ============

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and initiate parsing."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .docx files are allowed'}), 400

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save file
    filename = secure_filename(f"{job_id}_{file.filename}")
    filepath = get_upload_path(filename)
    file.save(str(filepath))

    # Parse the document
    try:
        parser = BiosketchParser(filepath)
        data = parser.parse()
        data_dict = data.to_dict()

        # Save to database or memory
        save_biosketch_data(job_id, data_dict)

        return jsonify({
            'job_id': job_id,
            'status': 'success',
            'redirect': url_for('main.review', job_id=job_id)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to parse document: {str(e)}'}), 500


@api_bp.route('/parse/<job_id>', methods=['GET'])
def get_parsed_data(job_id: str):
    """Get the parsed biosketch data for a job."""
    data = get_biosketch_data(job_id)
    if not data:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(data)


@api_bp.route('/parse/<job_id>', methods=['PUT'])
def update_parsed_data(job_id: str):
    """Update the parsed biosketch data (for manual edits)."""
    current_data = get_biosketch_data(job_id)
    if not current_data:
        return jsonify({'error': 'Job not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate and update
    try:
        # Merge updated fields
        current_data.update(data)

        # Extract selected items
        selected_contributions = data.get('selected_contributions')
        selected_products = data.get('selected_products')

        # Save updated data
        save_biosketch_data(job_id, current_data, selected_contributions, selected_products)

        return jsonify({'status': 'success', 'data': current_data})
    except Exception as e:
        return jsonify({'error': f'Failed to update data: {str(e)}'}), 500


@api_bp.route('/biosketch/<job_id>', methods=['DELETE'])
@login_required
def delete_biosketch(job_id: str):
    """Delete a saved biosketch."""
    from ..models import db, SavedBiosketch
    biosketch = SavedBiosketch.query.filter_by(job_id=job_id, user_id=current_user.id).first()

    if not biosketch:
        return jsonify({'error': 'Biosketch not found'}), 404

    db.session.delete(biosketch)
    db.session.commit()

    return jsonify({'status': 'success'})


@api_bp.route('/automate/<job_id>', methods=['POST'])
def start_automation(job_id: str):
    """Start the SciENcv automation process."""
    data = get_biosketch_data(job_id)
    if not data:
        return jsonify({'error': 'Job not found'}), 404

    # In a full implementation, this would trigger a Celery task
    # For now, we'll return the automation status endpoint
    return jsonify({
        'status': 'started',
        'job_id': job_id,
        'message': 'Automation will open a browser window. Please log in to SciENcv when prompted.',
        'sse_endpoint': url_for('api.automation_status', job_id=job_id)
    })


@api_bp.route('/automate/<job_id>/status', methods=['GET'])
def automation_status(job_id: str):
    """Get the status of an automation job (SSE endpoint)."""
    # This would be implemented as a Server-Sent Events endpoint
    # For now, return a simple status
    return jsonify({
        'job_id': job_id,
        'status': 'pending',
        'message': 'Automation not yet started'
    })


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})
