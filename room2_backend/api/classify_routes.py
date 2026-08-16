"""
classify_routes.py
POST /api/classify — run the trained RF classifier on a live session payload.
"""
from flask import Blueprint, request, jsonify
import joblib, os, sys
import numpy as np

# Add room3_features to path
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
sys.path.insert(0, os.path.join(PARENT_DIR, 'room3_features'))

from pipeline import extract_feature_vector

classify_bp = Blueprint('classify', __name__)

MODEL_PATH = os.path.join(PARENT_DIR, 'room4_classifier', 'saved_models', 'rf_model.pkl')
_model = None


def load_model():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
    return _model


@classify_bp.route('/classify', methods=['POST'])
def classify():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    model = load_model()
    if model is None:
        return jsonify({'error': 'Model not trained yet. Run room4_classifier/train.py first.'}), 503

    features = extract_feature_vector(data)
    X        = np.array(features).reshape(1, -1)
    pred     = model.predict(X)[0]
    proba    = model.predict_proba(X)[0].tolist()

    label_map = {0: 'human', 1: 'script', 2: 'llm'}
    return jsonify({
        'session_id':    data.get('session_id'),
        'prediction':    label_map.get(pred, 'unknown'),
        'class_id':      int(pred),
        'probabilities': {
            'human':  proba[0],
            'script': proba[1],
            'llm':    proba[2],
        }
    }), 200