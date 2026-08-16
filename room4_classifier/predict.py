"""
predict.py — Classify a single session JSON from the command line.

Usage:
    python room4_classifier/predict.py path/to/session.json
"""
import os, sys, json
import numpy as np
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../room3_features'))
from pipeline import extract_feature_vector, FEATURE_NAMES

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'saved_models/rf_model.pkl')
LABEL_MAP  = {0: 'human', 1: 'script', 2: 'llm'}


def predict_session(session: dict) -> dict:
    model    = joblib.load(MODEL_PATH)
    features = extract_feature_vector(session)
    X        = np.array(features).reshape(1, -1)
    pred     = model.predict(X)[0]
    proba    = model.predict_proba(X)[0]
    return {
        'prediction':    LABEL_MAP[pred],
        'class_id':      int(pred),
        'confidence':    float(proba[pred]),
        'probabilities': {
            'human':  float(proba[0]),
            'script': float(proba[1]),
            'llm':    float(proba[2]),
        },
        'feature_vector': dict(zip(FEATURE_NAMES, features)),
    }


def main():
    if len(sys.argv) < 2:
        print('Usage: python predict.py <session.json>')
        sys.exit(1)

    if not os.path.exists(MODEL_PATH):
        print('Model not found. Run train.py first.')
        sys.exit(1)

    with open(sys.argv[1]) as f:
        session = json.load(f)

    result = predict_session(session)

    print(f'\n── TIF Prediction ───────────────────────────────────')
    print(f'  Session    : {session.get("session_id", sys.argv[1])}')
    print(f'  Prediction : {result["prediction"].upper()}')
    print(f'  Confidence : {result["confidence"]:.1%}')
    print(f'  Probs      : human={result["probabilities"]["human"]:.3f}  '
          f'script={result["probabilities"]["script"]:.3f}  '
          f'llm={result["probabilities"]["llm"]:.3f}')
    print(f'\n── Feature Vector ───────────────────────────────────')
    for name, val in result['feature_vector'].items():
        print(f'  {name:35s}: {val:>10.2f}')


if __name__ == '__main__':
    main()