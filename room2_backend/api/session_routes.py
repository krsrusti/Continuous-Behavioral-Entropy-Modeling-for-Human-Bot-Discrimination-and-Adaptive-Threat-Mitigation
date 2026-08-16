"""
session_routes.py
POST  /api/session             — receive and persist a session payload
GET   /api/sessions            — list all stored sessions
PATCH /api/session/<id>/label  — assign a ground-truth label
"""
from flask import Blueprint, request, jsonify
from models.session_model import SessionModel
from database.db          import get_db

session_bp = Blueprint('session', __name__)


@session_bp.route('/session', methods=['POST'])
def receive_session():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    db   = get_db()
    sess = SessionModel.from_dict(data)
    db.add(sess)
    db.commit()
    return jsonify({'status': 'ok', 'session_id': sess.session_id}), 201


@session_bp.route('/sessions', methods=['GET'])
def list_sessions():
    db      = get_db()
    results = db.query(SessionModel).all()
    return jsonify([s.to_dict() for s in results]), 200


@session_bp.route('/session/<session_id>/label', methods=['PATCH'])
def label_session(session_id):
    """Manually assign a ground-truth label for the evaluation dataset."""
    data  = request.get_json()
    label = data.get('label')
    if label not in ('human', 'script', 'llm'):
        return jsonify({'error': 'label must be human | script | llm'}), 400
    db   = get_db()
    sess = db.query(SessionModel).filter_by(session_id=session_id).first()
    if not sess:
        return jsonify({'error': 'Not found'}), 404
    sess.label = label
    db.commit()
    return jsonify({'status': 'labelled', 'label': label}), 200