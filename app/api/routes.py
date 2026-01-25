"""API routes for biosketch parsing and automation."""

from __future__ import annotations
import os
import uuid
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for, g
from werkzeug.utils import secure_filename

from ..parser import BiosketchParser, BiosketchData
from ..firebase_config import firebase_auth_required, firebase_auth_optional
from ..firestore_models import (
    get_biosketch,
    get_biosketch_data as firestore_get_biosketch_data,
    save_biosketch,
    delete_biosketch as firestore_delete_biosketch,
    update_biosketch_data
)

# Try to import automation (only works if Playwright is installed)
try:
    from ..automation.sciencv_filler import run_automation
    import asyncio
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False
    run_automation = None


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


def get_biosketch_data_helper(job_id: str, user_id: str = None):
    """Get biosketch data from Firestore or memory.

    Tries Firestore first (with user_id if provided), falls back to memory.
    """
    # Try with user_id verification first
    if user_id:
        data = firestore_get_biosketch_data(job_id, user_id)
        if data:
            return data

    # Try Firestore without user_id verification (for direct page navigation)
    data = firestore_get_biosketch_data(job_id, None)
    if data:
        return data

    # Fall back to in-memory store
    return parsed_data_store.get(job_id)


def save_biosketch_data_helper(job_id: str, data: dict, user_id: str = None,
                               selected_contributions=None, selected_products=None,
                               edited_positions=None, edited_personal_statement=None,
                               edited_contributions=None, merge_history=None):
    """Save biosketch data to Firestore or memory."""
    if user_id:
        save_biosketch(job_id, data, user_id, selected_contributions, selected_products,
                       edited_positions, edited_personal_statement,
                       edited_contributions, merge_history)
    else:
        parsed_data_store[job_id] = data


# ============ Main Routes ============

@main_bp.route('/')
def index():
    """Render the main upload page."""
    return render_template('index.html')


@main_bp.route('/review/<job_id>')
@firebase_auth_optional
def review(job_id: str):
    """Render the review page for parsed biosketch data."""
    user_id = getattr(g, 'user_id', None)

    # Try to get data from Firestore or memory
    data = get_biosketch_data_helper(job_id, user_id)
    if not data:
        # Also try without user_id (for anonymous uploads)
        data = parsed_data_store.get(job_id)

    if not data:
        return render_template('error.html', message='Job not found'), 404

    # Get selected items and edited data from Firestore if user is logged in
    selected_contributions = []
    selected_products = {}
    edited_positions = None
    edited_personal_statement = None
    edited_contributions = None
    merge_history = None

    if user_id:
        biosketch = get_biosketch(job_id, user_id)
        if biosketch:
            selected_contributions = biosketch.get('selected_contributions') or []
            selected_products = biosketch.get('selected_products') or {}
            edited_positions = biosketch.get('edited_positions')
            edited_personal_statement = biosketch.get('edited_personal_statement')
            edited_contributions = biosketch.get('edited_contributions')
            merge_history = biosketch.get('merge_history')

    return render_template('review.html',
                           job_id=job_id,
                           data=data,
                           selected_contributions=selected_contributions,
                           selected_products=selected_products,
                           edited_positions=edited_positions,
                           edited_personal_statement=edited_personal_statement,
                           edited_contributions=edited_contributions,
                           merge_history=merge_history)


# ============ API Routes ============

@api_bp.route('/upload', methods=['POST'])
@firebase_auth_optional
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

        # Save to Firestore or memory
        user_id = getattr(g, 'user_id', None)
        save_biosketch_data_helper(job_id, data_dict, user_id)

        return jsonify({
            'job_id': job_id,
            'status': 'success',
            'redirect': url_for('main.review', job_id=job_id)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to parse document: {str(e)}'}), 500


@api_bp.route('/parse/<job_id>', methods=['GET'])
@firebase_auth_optional
def get_parsed_data(job_id: str):
    """Get the parsed biosketch data for a job."""
    user_id = getattr(g, 'user_id', None)
    data = get_biosketch_data_helper(job_id, user_id)

    if not data:
        # Try without user_id
        data = parsed_data_store.get(job_id)

    if not data:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(data)


@api_bp.route('/parse/<job_id>', methods=['PUT'])
@firebase_auth_optional
def update_parsed_data(job_id: str):
    """Update the parsed biosketch data (for manual edits)."""
    user_id = getattr(g, 'user_id', None)

    # Get current data
    current_data = get_biosketch_data_helper(job_id, user_id)
    if not current_data:
        current_data = parsed_data_store.get(job_id)

    if not current_data:
        return jsonify({'error': 'Job not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        # Merge updated fields into current data
        current_data.update(data)

        # Extract selected items
        selected_contributions = data.get('selected_contributions')
        selected_products = data.get('selected_products')

        # Extract user-edited data
        edited_positions = data.get('positions')
        edited_personal_statement = data.get('personal_statement')
        edited_contributions = data.get('contributions')
        merge_history = data.get('merge_history')

        # Save updated data with all edited fields
        save_biosketch_data_helper(job_id, current_data, user_id,
                                   selected_contributions, selected_products,
                                   edited_positions, edited_personal_statement,
                                   edited_contributions, merge_history)

        return jsonify({'status': 'success', 'saved_at': datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({'error': f'Failed to update data: {str(e)}'}), 500


@api_bp.route('/biosketch/<job_id>', methods=['DELETE'])
@firebase_auth_required
def delete_biosketch(job_id: str):
    """Delete a saved biosketch."""
    success = firestore_delete_biosketch(job_id, g.user_id)

    if not success:
        return jsonify({'error': 'Biosketch not found'}), 404

    return jsonify({'status': 'success'})


def run_automation_sync(data: dict, on_status=None):
    """Run the async automation synchronously."""
    if not AUTOMATION_AVAILABLE:
        return False

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_automation(data, headless=False, on_status=on_status))
    finally:
        loop.close()


@api_bp.route('/automate/<job_id>', methods=['POST'])
@firebase_auth_optional
def start_automation_route(job_id: str):
    """Start the SciENcv automation process.

    Automation requires Playwright to be installed locally.
    On Cloud Run, returns a message to use Claude in Chrome instead.
    """
    # Check if automation is available
    if not AUTOMATION_AVAILABLE:
        return jsonify({
            'status': 'coming_soon',
            'job_id': job_id,
            'message': 'Auto-fill requires running locally with Playwright installed. Please use "Copy JSON for Claude" and paste into Claude in Chrome to fill out your SciENcv form.'
        })

    user_id = getattr(g, 'user_id', None)

    # Get biosketch data
    data = get_biosketch_data_helper(job_id, user_id)
    if not data:
        data = parsed_data_store.get(job_id)

    if not data:
        return jsonify({'error': 'Job not found'}), 404

    # Start automation in background thread
    import threading
    import traceback

    def run_in_thread():
        log_file = '/tmp/sciencv_automation.log'

        def log(msg):
            with open(log_file, 'a') as f:
                f.write(f"{msg}\n")
            print(f"[Automation] {msg}")

        def status_callback(msg):
            log(msg)

        log(f"Thread started for job {job_id}")
        log(f"Data keys: {list(data.keys())}")

        try:
            log("Calling run_automation_sync...")
            success = run_automation_sync(data, on_status=status_callback)
            log(f"Completed: {'success' if success else 'failed'}")
        except Exception as e:
            log(f"Error: {e}")
            log(traceback.format_exc())

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()

    return jsonify({
        'status': 'started',
        'job_id': job_id,
        'message': 'Automation started. A browser window will open - please log in to SciENcv when prompted.'
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
