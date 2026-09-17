"""
risk_routes.py
POST /api/risk — classify a session and return risk score + action.
"""
from flask import Blueprint, request, jsonify
import joblib, os, sys
import numpy as np

# Add room3_features to path
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
sys.path.insert(0, os.path.join(PARENT_DIR, 'room3_features'))

from pipeline               import extract_feature_vector
from calculators.risk_score import evaluate_session, score_band

risk_bp = Blueprint('risk', __name__)

MODEL_PATH = os.path.join(PARENT_DIR, 'room4_classifier', 'saved_models', 'rf_model.pkl')
_model = None


def load_model():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
    return _model


@risk_bp.route('/risk', methods=['POST'])
def risk():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    model = load_model()
    if model is None:
        return jsonify({'error': 'Model not trained yet. Run room4_classifier/train.py first.'}), 503

    # ── Extract features ──────────────────────────────────────────────────
    try:
        features = extract_feature_vector(data)
    except Exception as e:
        return jsonify({'error': f'Feature extraction failed: {str(e)}'}), 500

    # ── Classify ──────────────────────────────────────────────────────────
    X    = np.array(features).reshape(1, -1)
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0].tolist()

    label_map     = {0: 'human', 1: 'bot', 2: 'llm'}
    prediction    = label_map[pred]
    probabilities = {
        'human':  proba[0],
        'bot':    proba[1],
        'llm':    proba[2],
    }

    # ── Compute risk score + action ───────────────────────────────────────
    result = evaluate_session(prediction, probabilities)

    # ── Build response ────────────────────────────────────────────────────
    response = {
        'session_id':    data.get('session_id'),
        'score':         result['score'],
        'band':          score_band(result['score']),
        'action':        result['action'],
        'label':         result['label'],
        'description':   result['description'],
        'color':         result['color'],
        'prediction':    result['prediction'],
        'probabilities': result['probabilities'],
        'features': {
            'mean_probe_reaction_time': round(features[4], 2),
            'probe_reaction_variance':  round(features[5], 2),
            'action_burstiness_score':  round(features[6], 2),
        }
    }

    return jsonify(response), 200


@risk_bp.route('/risk/batch', methods=['POST'])
def risk_batch():
    """
    POST /api/risk/batch
    Classify multiple sessions at once.
    Body: { "sessions": [ session1, session2, ... ] }
    """
    data     = request.get_json(force=True, silent=True)
    sessions = data.get('sessions', []) if data else []

    if not sessions:
        return jsonify({'error': 'No sessions provided'}), 400

    model = load_model()
    if model is None:
        return jsonify({'error': 'Model not trained yet.'}), 503

    results = []
    for session in sessions:
        try:
            features      = extract_feature_vector(session)
            X             = np.array(features).reshape(1, -1)
            pred          = model.predict(X)[0]
            proba         = model.predict_proba(X)[0].tolist()
            label_map     = {0: 'human', 1: 'bot', 2: 'llm'}
            prediction    = label_map[pred]
            probabilities = {'human': proba[0], 'bot': proba[1], 'llm': proba[2]}
            result        = evaluate_session(prediction, probabilities)
            results.append({
                'session_id': session.get('session_id'),
                **result,
            })
        except Exception as e:
            results.append({
                'session_id': session.get('session_id'),
                'error':      str(e),
            })

    return jsonify({'results': results, 'total': len(results)}), 200