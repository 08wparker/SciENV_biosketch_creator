"""API routes for biosketch parsing and automation."""

from __future__ import annotations
import os
import uuid
import json
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for
from werkzeug.utils import secure_filename

from ..parser import BiosketchParser, BiosketchData


# Create blueprints
api_bp = Blueprint('api', __name__)
main_bp = Blueprint('main', __name__)

# In-memory storage for parsed data (in production, use Redis or database)
parsed_data_store = {}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def get_upload_path(filename: str) -> Path:
    """Get the full path for an uploaded file."""
    return Path(current_app.config['UPLOAD_FOLDER']) / filename


# ============ Main Routes ============

@main_bp.route('/')
def index():
    """Render the main upload page."""
    return render_template('index.html')


@main_bp.route('/review/<job_id>')
def review(job_id: str):
    """Render the review page for parsed biosketch data."""
    if job_id not in parsed_data_store:
        return render_template('error.html', message='Job not found'), 404

    data = parsed_data_store[job_id]
    return render_template('review.html', job_id=job_id, data=data)


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
        parsed_data_store[job_id] = data.to_dict()

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
    if job_id not in parsed_data_store:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(parsed_data_store[job_id])


@api_bp.route('/parse/<job_id>', methods=['PUT'])
def update_parsed_data(job_id: str):
    """Update the parsed biosketch data (for manual edits)."""
    if job_id not in parsed_data_store:
        return jsonify({'error': 'Job not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate and update
    try:
        # Merge updated fields
        current_data = parsed_data_store[job_id]
        current_data.update(data)
        parsed_data_store[job_id] = current_data

        return jsonify({'status': 'success', 'data': current_data})
    except Exception as e:
        return jsonify({'error': f'Failed to update data: {str(e)}'}), 500


@api_bp.route('/automate/<job_id>', methods=['POST'])
def start_automation(job_id: str):
    """Start the SciENcv automation process."""
    if job_id not in parsed_data_store:
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
