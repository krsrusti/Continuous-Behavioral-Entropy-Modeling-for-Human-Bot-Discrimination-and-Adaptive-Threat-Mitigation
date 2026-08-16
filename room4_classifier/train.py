"""
train.py — Train the Random Forest classifier.

Usage:
    python room4_classifier/train.py

Reads labelled JSON files from data/sessions/.
Runs ablation study (BEI-only vs BEI+TIF).
Saves model to room4_classifier/saved_models/rf_model.pkl.
"""
import os, sys, json, glob
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../room3_features'))
from pipeline import extract_feature_vector, FEATURE_NAMES

LABEL_MAP    = {'human': 0, 'script': 1, 'llm': 2}
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), '../data/sessions')
MODEL_OUT    = os.path.join(os.path.dirname(__file__), 'saved_models/rf_model.pkl')

BEI_IDX = [0, 1, 2, 3]
TIF_IDX = [4, 5, 6, 7, 8]


def load_dataset():
    X, y = [], []
    files = [f for f in glob.glob(os.path.join(SESSIONS_DIR, '*.json'))
             if os.path.getsize(f) > 100]
    for path in files:
        with open(path) as f:
            session = json.load(f)
        label = session.get('label')
        if label not in LABEL_MAP:
            print(f'  Skipping {os.path.basename(path)}: unknown label "{label}"')
            continue
        X.append(extract_feature_vector(session))
        y.append(LABEL_MAP[label])
    return np.array(X), np.array(y)


def run_cv(X, y, feature_set='all'):
    X_use = X[:, BEI_IDX] if feature_set == 'bei' else X
    label = 'BEI-only' if feature_set == 'bei' else 'BEI + TIF'
    rf    = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    cv    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    acc   = cross_val_score(rf, X_use, y, cv=cv, scoring='accuracy')
    print(f'  [{label:10s}]  CV Accuracy: {acc.mean():.3f} ± {acc.std():.3f}')
    rf.fit(X_use, y)
    return rf


def print_feature_importance(model):
    importances = model.feature_importances_
    print('\n── Feature Importances ─────────────────────────────')
    ranked = sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1])
    for name, imp in ranked:
        bar = '█' * int(imp * 50)
        print(f'  {name:35s} {imp:.4f}  {bar}')


def main():
    print('Loading dataset …')
    X, y = load_dataset()
    if len(X) == 0:
        print('\nNo labelled sessions found in data/sessions/.')
        print('Run: python scripts/generate_synthetic_sessions.py')
        return

    print(f'Dataset: {len(X)} sessions')
    print(f'Classes: human={sum(y==0)}  script={sum(y==1)}  llm={sum(y==2)}')

    print('\n── Ablation Study ──────────────────────────────────')
    run_cv(X, y, feature_set='bei')
    rf_full = run_cv(X, y, feature_set='all')

    print_feature_importance(rf_full)

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    joblib.dump(rf_full, MODEL_OUT)
    print(f'\n✅ Model saved → {MODEL_OUT}')


if __name__ == '__main__':
    main()