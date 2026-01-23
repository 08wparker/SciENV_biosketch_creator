"""Firestore data models and CRUD operations for biosketch storage."""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from .firebase_config import get_firestore_client


# Collection names
BIOSKETCHES_COLLECTION = 'biosketches'


def get_biosketch(job_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get a biosketch by job_id.

    Args:
        job_id: The unique job identifier
        user_id: Optional user ID to verify ownership

    Returns:
        Biosketch data dict or None if not found
    """
    db = get_firestore_client()
    doc_ref = db.collection(BIOSKETCHES_COLLECTION).document(job_id)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = doc.to_dict()

    # If user_id provided, verify ownership
    if user_id and data.get('user_id') != user_id:
        return None

    return data


def get_user_biosketches(user_id: str) -> List[Dict[str, Any]]:
    """Get all biosketches for a user.

    Args:
        user_id: Firebase Auth UID

    Returns:
        List of biosketch data dicts, ordered by updated_at descending
    """
    db = get_firestore_client()
    # Simple query without order_by to avoid needing a composite index
    docs = (db.collection(BIOSKETCHES_COLLECTION)
            .where('user_id', '==', user_id)
            .stream())

    results = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    # Sort in Python by updated_at descending
    results.sort(key=lambda x: x.get('updated_at') or '', reverse=True)
    return results


def save_biosketch(
    job_id: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None,
    selected_contributions: Optional[List[int]] = None,
    selected_products: Optional[Dict[str, List[int]]] = None
) -> Dict[str, Any]:
    """Save or update a biosketch.

    Args:
        job_id: Unique job identifier (used as document ID)
        data: Parsed biosketch data
        user_id: Firebase Auth UID (None for anonymous)
        selected_contributions: List of selected contribution indices
        selected_products: Dict with 'related' and 'other' product indices

    Returns:
        The saved document data
    """
    db = get_firestore_client()
    doc_ref = db.collection(BIOSKETCHES_COLLECTION).document(job_id)

    doc_data = {
        'job_id': job_id,
        'data': data,
        'name': data.get('name', 'Unnamed Biosketch'),
        'updated_at': SERVER_TIMESTAMP
    }

    # Only set user_id if provided
    if user_id:
        doc_data['user_id'] = user_id

    # Only set selections if provided
    if selected_contributions is not None:
        doc_data['selected_contributions'] = selected_contributions
    if selected_products is not None:
        doc_data['selected_products'] = selected_products

    # Check if document exists
    existing = doc_ref.get()
    if not existing.exists:
        doc_data['created_at'] = SERVER_TIMESTAMP

    # Merge to preserve existing fields
    doc_ref.set(doc_data, merge=True)

    return doc_data


def delete_biosketch(job_id: str, user_id: str) -> bool:
    """Delete a biosketch.

    Args:
        job_id: The unique job identifier
        user_id: Firebase Auth UID (for ownership verification)

    Returns:
        True if deleted, False if not found or not owned by user
    """
    db = get_firestore_client()
    doc_ref = db.collection(BIOSKETCHES_COLLECTION).document(job_id)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    # Verify ownership
    if doc.to_dict().get('user_id') != user_id:
        return False

    doc_ref.delete()
    return True


def get_biosketch_data(job_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get just the parsed biosketch data.

    Args:
        job_id: The unique job identifier
        user_id: Optional user ID to verify ownership

    Returns:
        Parsed biosketch data or None
    """
    biosketch = get_biosketch(job_id, user_id)
    if biosketch:
        return biosketch.get('data')
    return None


def update_biosketch_data(
    job_id: str,
    updates: Dict[str, Any],
    user_id: Optional[str] = None
) -> bool:
    """Update specific fields in a biosketch.

    Args:
        job_id: The unique job identifier
        updates: Dict of fields to update
        user_id: Optional user ID to verify ownership

    Returns:
        True if updated, False if not found
    """
    db = get_firestore_client()
    doc_ref = db.collection(BIOSKETCHES_COLLECTION).document(job_id)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    # If user_id provided, verify ownership
    if user_id:
        existing_data = doc.to_dict()
        if existing_data.get('user_id') and existing_data['user_id'] != user_id:
            return False

    updates['updated_at'] = SERVER_TIMESTAMP
    doc_ref.update(updates)
    return True
