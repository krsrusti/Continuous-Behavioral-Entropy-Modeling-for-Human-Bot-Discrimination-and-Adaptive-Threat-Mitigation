"""
experiment_routes.py

POST /api/experiment/start   — researcher creates an experiment before browser session
GET  /api/experiments        — list all experiments (researcher dashboard)
GET  /api/experiment/<id>    — get one experiment (researcher use only)
PATCH /api/experiment/<id>/complete — manually mark as completed

SECURITY RULES:
  - POST /api/experiment/start returns to_browser_dict() — no agent_class
  - GET  /api/experiments      returns to_dict()         — includes agent_class
  - GET  /api/experiment/<id>  returns to_dict()         — includes agent_class

The researcher calls POST /api/experiment/start before each session.
The response is passed to TIFSession.init() in the browser.
The browser never sees agent_class.
"""
from flask import Blueprint, request, jsonify

from models.experiment_model import ExperimentModel, VALID_AGENT_CLASSES, VALID_TASK_IDS
from database.db             import get_db

experiment_bp = Blueprint('experiment', __name__)


# ── POST /api/experiment/start ────────────────────────────────────────────────

@experiment_bp.route('/experiment/start', methods=['POST'])
def start_experiment():
    """
    Researcher calls this before each session to register:
      - agent_class   (human | bot | llm)
      - task_id       (login | checkout | search | navigation)
      - probe_enabled (true | false)
      - notes         (optional)

    Returns a browser-safe dict — agent_class is NOT included.

    Example request:
        POST /api/experiment/start
        {
            "agent_class":   "human",
            "task_id":       "login",
            "probe_enabled": true,
            "notes":         "participant 1, probe on condition"
        }

    Example response (safe for browser):
        {
            "experiment_id":  "exp_abc123",
            "participant_id": "p_xyz789",
            "task_id":        "login",
            "probe_enabled":  true
        }
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    agent_class   = data.get('agent_class')
    task_id       = data.get('task_id')
    probe_enabled = data.get('probe_enabled')
    notes         = data.get('notes')

    # ── Validate ──────────────────────────────────────────────────────────────
    errors = []

    if not agent_class:
        errors.append('agent_class is required')
    elif agent_class not in VALID_AGENT_CLASSES:
        errors.append(f'agent_class must be one of {sorted(VALID_AGENT_CLASSES)}')

    if not task_id:
        errors.append('task_id is required')
    elif task_id not in VALID_TASK_IDS:
        errors.append(f'task_id must be one of {sorted(VALID_TASK_IDS)}')

    if probe_enabled is None:
        errors.append('probe_enabled is required (true or false)')
    elif not isinstance(probe_enabled, bool):
        errors.append('probe_enabled must be a boolean (true or false)')

    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    # ── Create experiment ─────────────────────────────────────────────────────
    try:
        experiment = ExperimentModel.create(
            agent_class   = agent_class,
            task_id       = task_id,
            probe_enabled = probe_enabled,
            notes         = notes,
        )
        db = get_db()
        db.add(experiment)
        db.commit()
        db.refresh(experiment)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': f'Failed to create experiment: {str(e)}'}), 500

    # ── Return browser-safe dict — NO agent_class ─────────────────────────────
    return jsonify(experiment.to_browser_dict()), 201


# ── GET /api/experiments ──────────────────────────────────────────────────────

@experiment_bp.route('/experiments', methods=['GET'])
def list_experiments():
    """
    List all experiments — researcher dashboard only.
    Returns full dict including agent_class.

    Optional query params:
        ?agent_class=human     filter by agent class
        ?task_id=login         filter by task
        ?probe_enabled=true    filter by probe condition
        ?completed=false       filter by completion status
    """
    db = get_db()
    q  = db.query(ExperimentModel)

    # Filters
    agent_class   = request.args.get('agent_class')
    task_id       = request.args.get('task_id')
    probe_enabled = request.args.get('probe_enabled')
    completed     = request.args.get('completed')

    if agent_class:
        q = q.filter(ExperimentModel.agent_class == agent_class)
    if task_id:
        q = q.filter(ExperimentModel.task_id == task_id)
    if probe_enabled is not None:
        q = q.filter(ExperimentModel.probe_enabled == (probe_enabled.lower() == 'true'))
    if completed is not None:
        q = q.filter(ExperimentModel.completed == (completed.lower() == 'true'))

    experiments = q.order_by(ExperimentModel.created_at.desc()).all()

    # Summary stats
    total     = len(experiments)
    completed_count = sum(1 for e in experiments if e.completed)
    pending   = total - completed_count

    by_class  = {}
    for e in experiments:
        by_class[e.agent_class] = by_class.get(e.agent_class, 0) + 1

    return jsonify({
        'experiments': [e.to_dict() for e in experiments],
        'summary': {
            'total':     total,
            'completed': completed_count,
            'pending':   pending,
            'by_class':  by_class,
        }
    }), 200


# ── GET /api/experiment/<id> ──────────────────────────────────────────────────

@experiment_bp.route('/experiment/<experiment_id>', methods=['GET'])
def get_experiment(experiment_id):
    """
    Get one experiment by ID — researcher use only.
    Returns full dict including agent_class.
    """
    db         = get_db()
    experiment = db.query(ExperimentModel).filter_by(
        experiment_id=experiment_id
    ).first()

    if not experiment:
        return jsonify({'error': f'Experiment {experiment_id} not found'}), 404

    return jsonify(experiment.to_dict()), 200


# ── PATCH /api/experiment/<id>/complete ───────────────────────────────────────

@experiment_bp.route('/experiment/<experiment_id>/complete', methods=['PATCH'])
def complete_experiment(experiment_id):
    """
    Manually mark an experiment as completed.
    Normally this happens automatically when a session arrives.
    Use this if a session was submitted without an experiment_id.
    """
    data       = request.get_json(force=True, silent=True) or {}
    session_id = data.get('session_id')

    db         = get_db()
    experiment = db.query(ExperimentModel).filter_by(
        experiment_id=experiment_id
    ).first()

    if not experiment:
        return jsonify({'error': f'Experiment {experiment_id} not found'}), 404

    experiment.mark_completed(session_id or 'manual')
    db.commit()

    return jsonify({
        'status':        'completed',
        'experiment_id': experiment_id,
        'session_id':    experiment.session_id,
    }), 200


# ── GET /api/experiment/stats ─────────────────────────────────────────────────

@experiment_bp.route('/experiments/stats', methods=['GET'])
def experiment_stats():
    """
    Pilot dataset progress summary.
    Shows how many sessions have been collected per condition.

    Useful for tracking progress toward the 30-session pilot target:
        Human  + probe ON:  target 5
        Human  + probe OFF: target 5
        Bot    + probe ON:  target 5
        Bot    + probe OFF: target 5
        LLM    + probe ON:  target 5
        LLM    + probe OFF: target 5
    """
    db          = get_db()
    experiments = db.query(ExperimentModel).all()

    # Build condition matrix
    conditions = {}
    for agent_class in ['human', 'bot', 'llm']:
        for probe in [True, False]:
            key = f'{agent_class}_probe_{"on" if probe else "off"}'
            matching = [e for e in experiments
                        if e.agent_class   == agent_class
                        and e.probe_enabled == probe]
            conditions[key] = {
                'total':     len(matching),
                'completed': sum(1 for e in matching if e.completed),
                'pending':   sum(1 for e in matching if not e.completed),
            }

    return jsonify({
        'conditions': conditions,
        'pilot_target': 5,
        'total_target': 30,
    }), 200