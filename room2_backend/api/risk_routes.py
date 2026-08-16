"""
risk_routes.py
POST /api/risk — classify a session and return risk score + action.
"""
from flask import Blueprint, request, jsonify
import joblib, os, sys
import numpy as np

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
sys.path.insert(0, os.path.join(PARENT_DIR, 'room3_features'))

from pipeline                    import extract_feature_vector
from calculators.risk_score      import evaluate_session

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
        return jsonify({'error': 'Model not trained yet.'}), 503

    # Extract features and classify
    features = extract_feature_vector(data)
    X        = np.array(features).reshape(1, -1)
    pred     = model.predict(X)[0]
    proba    = model.predict_proba(X)[0].tolist()

    label_map = {0: 'human', 1: 'script', 2: 'llm'}
    prediction    = label_map[pred]
    probabilities = {
        'human':  proba[0],
        'script': proba[1],
        'llm':    proba[2],
    }

    # Compute risk score and action
    result = evaluate_session(prediction, probabilities)
    result['session_id'] = data.get('session_id')

    return jsonify(result), 200