"""session_routes.py"""
from flask import Blueprint, request, jsonify
from models.session_model    import SessionModel
from models.experiment_model import ExperimentModel
from database.db             import get_db

session_bp = Blueprint('session', __name__)


@session_bp.route('/session', methods=['POST'])
def receive_session():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    db = get_db()

    # ── Look up experiment — agent_class comes from here only ─────────────────
    experiment    = None
    experiment_id = data.get('experiment_id')

    if experiment_id:
        experiment = db.query(ExperimentModel).filter_by(
            experiment_id=experiment_id
        ).first()
        if not experiment:
            print(f'[TIF] Warning: experiment_id {experiment_id} not found.')
        elif experiment.completed:
            print(f'[TIF] Warning: experiment {experiment_id} already completed.')

    # ── Build session ─────────────────────────────────────────────────────────
    try:
        sess = SessionModel.from_dict(data, experiment=experiment)
    except Exception as e:
        return jsonify({'error': f'Failed to build session: {str(e)}'}), 400

    # ── Handle duplicate ──────────────────────────────────────────────────────
    existing = db.query(SessionModel).filter_by(
        session_id=sess.session_id
    ).first()

    if existing:
        existing.end_time       = sess.end_time
        existing.passive_events = sess.passive_events
        existing.probes         = sess.probes
        if sess.agent_class and not existing.agent_class:
            existing.agent_class = sess.agent_class
            existing.label       = sess.agent_class
        db.commit()
        return jsonify({
            'status':        'updated',
            'session_id':    existing.session_id,
            'agent_class':   existing.agent_class,
            'probe_enabled': existing.probe_enabled,
        }), 200

    # ── Save session ──────────────────────────────────────────────────────────
    db.add(sess)

    # ── Mark experiment completed ─────────────────────────────────────────────
    if experiment and not experiment.completed:
        experiment.mark_completed(sess.session_id)

    db.commit()

    return jsonify({
        'status':        'ok',
        'session_id':    sess.session_id,
        'agent_class':   sess.agent_class,
        'probe_enabled': sess.probe_enabled,
    }), 201


@session_bp.route('/sessions', methods=['GET'])
def list_sessions():
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


@session_bp.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    db   = get_db()
    sess = db.query(SessionModel).filter_by(session_id=session_id).first()
    if not sess:
        return jsonify({'error': f'Session {session_id} not found'}), 404
    return jsonify(sess.to_dict()), 200


@session_bp.route('/session/<session_id>/label', methods=['PATCH'])
def label_session(session_id):
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

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
    sess.label       = agent_class
    db.commit()
    return jsonify({
        'status':      'labelled',
        'session_id':  session_id,
        'agent_class': agent_class,
    }), 200


@session_bp.route('/sessions/stats', methods=['GET'])
def session_stats():
    db       = get_db()
    sessions = db.query(SessionModel).all()
    total     = len(sessions)
    labelled  = [s for s in sessions if s.agent_class]
    unlabelled = [s for s in sessions if not s.agent_class]

    by_class = {}
    for cls in ['human', 'bot', 'llm']:
        matching = [s for s in labelled if s.agent_class == cls]
        by_class[cls] = {
            'total':     len(matching),
            'probe_on':  sum(1 for s in matching if s.probe_enabled),
            'probe_off': sum(1 for s in matching if s.probe_enabled is False),
        }

    by_task = {}
    for task in ['login', 'checkout', 'search', 'navigation']:
        by_task[task] = sum(1 for s in sessions if s.task_id == task)

    return jsonify({
        'total':      total,
        'labelled':   len(labelled),
        'unlabelled': len(unlabelled),
        'by_class':   by_class,
        'by_task':    by_task,
    }), 200