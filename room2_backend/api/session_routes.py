"""
session_routes.py

POST  /api/session             — receive session from browser, stamp agent_class from experiment
GET   /api/sessions            — list all sessions (researcher dashboard)
GET   /api/session/<id>        — get one session
PATCH /api/session/<id>/label  — manually assign agent_class (fallback if no experiment)

CRITICAL RULE:
  agent_class is NEVER taken from the browser payload (d).
  It is always stamped from the experiment record looked up by experiment_id.
  If no experiment_id is present, agent_class stays null until manually labelled.
"""
from flask import Blueprint, request, jsonify

from models.session_model    import SessionModel
from models.experiment_model import ExperimentModel
from database.db             import get_db

session_bp = Blueprint('session', __name__)


# ── POST /api/session ─────────────────────────────────────────────────────────

@session_bp.route('/session', methods=['POST'])
def receive_session():
    """
    Receive a session payload from the browser.

    Steps:
      1. Parse and validate the payload
      2. Look up experiment by experiment_id (if provided)
      3. Stamp agent_class from experiment — NEVER from payload
      4. Save session to DB
      5. Mark experiment as completed
      6. Return session_id confirmation

    agent_class is never trusted from the browser.
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    db = get_db()

    # ── Step 1: Look up experiment ────────────────────────────────────────────
    experiment    = None
    experiment_id = data.get('experiment_id')

    if experiment_id:
        experiment = db.query(ExperimentModel).filter_by(
            experiment_id=experiment_id
        ).first()

        if not experiment:
            # Experiment ID provided but not found — warn but continue
            print(f'[TIF] Warning: experiment_id {experiment_id} not found. '
                  f'agent_class will be null.')

        elif experiment.completed:
            # Experiment already has a session — possible duplicate
            print(f'[TIF] Warning: experiment {experiment_id} already completed. '
                  f'Possible duplicate session.')

    # ── Step 2: Build session — agent_class from experiment only ──────────────
    try:
        sess = SessionModel.from_dict(data, experiment=experiment)
    except Exception as e:
        return jsonify({'error': f'Failed to build session: {str(e)}'}), 400

    # ── Step 3: Check for duplicate session_id ────────────────────────────────
    existing = db.query(SessionModel).filter_by(
        session_id=sess.session_id
    ).first()

    if existing:
        # Update existing rather than creating a duplicate
        # (can happen if sendBeacon fires after fetch)
        existing.end_time       = sess.end_time
        existing.passive_events = sess.passive_events
        existing.probes         = sess.probes
        if sess.agent_class and not existing.agent_class:
            existing.agent_class = sess.agent_class
            existing.label       = sess.agent_class
        db.commit()
        return jsonify({
            'status':     'updated',
            'session_id': existing.session_id,
            'agent_class': existing.agent_class,
        }), 200

    # ── Step 4: Save session ──────────────────────────────────────────────────
    db.add(sess)

    # ── Step 5: Mark experiment completed ────────────────────────────────────
    if experiment and not experiment.completed:
        experiment.mark_completed(sess.session_id)

    db.commit()

    return jsonify({
        'status':      'ok',
        'session_id':  sess.session_id,
        'agent_class': sess.agent_class,   # null if no experiment
        'probe_enabled': sess.probe_enabled,
    }), 201


# ── GET /api/sessions ─────────────────────────────────────────────────────────

@session_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """
    List all sessions.

    Optional query params:
        ?agent_class=human
        ?task_id=login
        ?probe_enabled=true
        ?labelled=true        only sessions with agent_class set
        ?labelled=false       only sessions without agent_class
    """
    db = get_db()
    q  = db.query(SessionModel)

    agent_class   = request.args.get('agent_class')
    task_id       = request.args.get('task_id')
    probe_enabled = request.args.get('probe_enabled')
    labelled      = request.args.get('labelled')

    if agent_class:
        q = q.filter(SessionModel.agent_class == agent_class)
    if task_id:
        q = q.filter(SessionModel.task_id == task_id)
    if probe_enabled is not None:
        q = q.filter(SessionModel.probe_enabled == (probe_enabled.lower() == 'true'))
    if labelled is not None:
        if labelled.lower() == 'true':
            q = q.filter(SessionModel.agent_class.isnot(None))
        else:
            q = q.filter(SessionModel.agent_class.is_(None))

    sessions = q.order_by(SessionModel.created_at.desc()).all()

    return jsonify([s.to_dict() for s in sessions]), 200


# ── GET /api/session/<id> ─────────────────────────────────────────────────────

@session_bp.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get one session by ID."""
    db   = get_db()
    sess = db.query(SessionModel).filter_by(session_id=session_id).first()

    if not sess:
        return jsonify({'error': f'Session {session_id} not found'}), 404

    return jsonify(sess.to_dict()), 200


# ── PATCH /api/session/<id>/label ────────────────────────────────────────────

@session_bp.route('/session/<session_id>/label', methods=['PATCH'])
def label_session(session_id):
    """
    Manually assign agent_class to a session.

    Use this as a fallback when:
      - No experiment_id was provided (browser error)
      - Experiment record was missing
      - You need to correct a wrong label

    Body: { "agent_class": "human" | "bot" | "llm" }

    Also accepts legacy field name "label" for backward compatibility.
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    # Accept both 'agent_class' and legacy 'label'
    agent_class = data.get('agent_class') or data.get('label')

    if not agent_class:
        return jsonify({'error': 'agent_class is required'}), 400

    if agent_class not in ('human', 'bot', 'llm'):
        return jsonify({'error': 'agent_class must be human | bot | llm'}), 400

    db   = get_db()
    sess = db.query(SessionModel).filter_by(session_id=session_id).first()

    if not sess:
        return jsonify({'error': f'Session {session_id} not found'}), 404

    sess.agent_class = agent_class
    sess.label       = agent_class   # keep in sync
    db.commit()

    return jsonify({
        'status':      'labelled',
        'session_id':  session_id,
        'agent_class': agent_class,
    }), 200


# ── GET /api/sessions/stats ───────────────────────────────────────────────────

@session_bp.route('/sessions/stats', methods=['GET'])
def session_stats():
    """
    Dataset composition summary.
    Shows labelled vs unlabelled, probe ON vs OFF, per class breakdown.
    Useful for monitoring pilot collection progress.
    """
    db       = get_db()
    sessions = db.query(SessionModel).all()

    total     = len(sessions)
    labelled  = [s for s in sessions if s.agent_class]
    unlabelled = [s for s in sessions if not s.agent_class]

    # Per class
    by_class = {}
    for cls in ['human', 'bot', 'llm']:
        matching = [s for s in labelled if s.agent_class == cls]
        by_class[cls] = {
            'total':     len(matching),
            'probe_on':  sum(1 for s in matching if s.probe_enabled),
            'probe_off': sum(1 for s in matching if s.probe_enabled is False),
        }

    # Per task
    by_task = {}
    for task in ['login', 'checkout', 'search', 'navigation']:
        matching = [s for s in sessions if s.task_id == task]
        by_task[task] = len(matching)

    return jsonify({
        'total':       total,
        'labelled':    len(labelled),
        'unlabelled':  len(unlabelled),
        'by_class':    by_class,
        'by_task':     by_task,
    }), 200