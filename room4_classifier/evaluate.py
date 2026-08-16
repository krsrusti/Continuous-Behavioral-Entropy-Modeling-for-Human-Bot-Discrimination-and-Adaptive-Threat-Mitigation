"""
evaluate.py — Full classification report + confusion matrix.

Usage:
    python room4_classifier/evaluate.py
"""
import os, sys, json, glob
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../room3_features'))
from pipeline import extract_feature_vector

MODEL_PATH   = os.path.join(os.path.dirname(__file__), 'saved_models/rf_model.pkl')
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), '../data/sessions')
LABEL_MAP    = {'human': 0, 'script': 1, 'llm': 2}
LABEL_NAMES  = ['human', 'script', 'llm']


def main():
    if not os.path.exists(MODEL_PATH):
        print('Model not found. Run train.py first.')
        return

    model = joblib.load(MODEL_PATH)

    X, y = [], []
    files = [f for f in glob.glob(os.path.join(SESSIONS_DIR, '*.json'))
             if os.path.getsize(f) > 100]
    for path in files:
        with open(path) as f:
            session = json.load(f)
        label = session.get('label')
        if label not in LABEL_MAP:
            continue
        X.append(extract_feature_vector(session))
        y.append(LABEL_MAP[label])

    X, y  = np.array(X), np.array(y)
    preds = model.predict(X)

    print('── Classification Report ────────────────────────────')
    print(classification_report(y, preds, target_names=LABEL_NAMES))

    print('── Confusion Matrix ─────────────────────────────────')
    cm = confusion_matrix(y, preds)
    print(f'{"":>10}  {"human":>8}  {"script":>8}  {"llm":>8}')
    for row_label, row in zip(LABEL_NAMES, cm):
        print(f'{row_label:>10}  {row[0]:>8}  {row[1]:>8}  {row[2]:>8}')

    print('\n── Per-class Accuracy ───────────────────────────────')
    for i, name in enumerate(LABEL_NAMES):
        mask    = y == i
        correct = (preds[mask] == y[mask]).sum()
        total   = mask.sum()
        print(f'  {name:8s}: {correct}/{total}  ({correct/total:.1%})')


if __name__ == '__main__':
    main()