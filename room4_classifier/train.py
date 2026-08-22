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
from sklearn.ensemble        import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics         import classification_report, confusion_matrix

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../room3_features'))

from pipeline import extract_feature_vector, FEATURE_NAMES

LABEL_MAP    = {'human': 0, 'script': 1, 'llm': 2}
LABEL_NAMES  = ['human', 'script', 'llm']
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), '../data/sessions')
MODEL_OUT    = os.path.join(os.path.dirname(__file__), 'saved_models/rf_model.pkl')

BEI_IDX = [0, 1, 2, 3]
TIF_IDX = [4, 5, 6, 7, 8]


# ── Load dataset ──────────────────────────────────────────────────────────────

def load_dataset():
    X, y = [], []
    files = [f for f in glob.glob(os.path.join(SESSIONS_DIR, '*.json'))
             if os.path.getsize(f) > 100]

    skipped = 0
    for path in files:
        with open(path) as f:
            session = json.load(f)
        label = session.get('label')
        if label not in LABEL_MAP:
            skipped += 1
            continue
        try:
            features = extract_feature_vector(session)
            X.append(features)
            y.append(LABEL_MAP[label])
        except Exception as e:
            print(f'  Warning: could not extract features from {os.path.basename(path)}: {e}')
            skipped += 1

    if skipped > 0:
        print(f'  Skipped {skipped} unlabelled or invalid sessions')

    return np.array(X), np.array(y)


# ── Cross validation ──────────────────────────────────────────────────────────

def run_cv(X, y, feature_set='all'):
    X_use = X[:, BEI_IDX] if feature_set == 'bei' else X
    label = 'BEI-only' if feature_set == 'bei' else 'BEI + TIF'

    rf  = RandomForestClassifier(
        n_estimators = 200,
        max_depth    = None,
        random_state = 42,
        n_jobs       = -1,
    )
    cv  = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    acc = cross_val_score(rf, X_use, y, cv=cv, scoring='accuracy')

    print(f'  [{label:10s}]  CV Accuracy: {acc.mean():.3f} ± {acc.std():.3f}')

    # Fit on full data for saving
    rf.fit(X_use, y)
    return rf


# ── Feature importance ────────────────────────────────────────────────────────

def print_feature_importance(model):
    importances = model.feature_importances_
    print('\n── Feature Importances ─────────────────────────────')
    ranked = sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1])
    for name, imp in ranked:
        bar = '█' * int(imp * 50)
        print(f'  {name:35s} {imp:.4f}  {bar}')


# ── Full evaluation ───────────────────────────────────────────────────────────

def print_evaluation(model, X, y):
    preds = model.predict(X)
    print('\n── Classification Report ────────────────────────────')
    print(classification_report(y, preds, target_names=LABEL_NAMES))
    print('── Confusion Matrix ─────────────────────────────────')
    cm = confusion_matrix(y, preds)
    print(f'{"":>10}  {"human":>8}  {"script":>8}  {"llm":>8}')
    for row_label, row in zip(LABEL_NAMES, cm):
        print(f'{row_label:>10}  {row[0]:>8}  {row[1]:>8}  {row[2]:>8}')
    print('\n── Per-class Accuracy ───────────────────────────────')
    for i, name in enumerate(LABEL_NAMES):
        mask    = y == i
        if mask.sum() == 0:
            print(f'  {name:8s}: no samples')
            continue
        correct = (preds[mask] == y[mask]).sum()
        total   = mask.sum()
        print(f'  {name:8s}: {correct}/{total}  ({correct/total:.1%})')


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print('Loading dataset …')
    X, y = load_dataset()

    if len(X) == 0:
        print('\nNo labelled sessions found in data/sessions/.')
        print('Options:')
        print('  1. Run: python scripts/generate_synthetic_sessions.py')
        print('  2. Collect real sessions and label them in the dashboard')
        return

    print(f'Dataset  : {len(X)} sessions')
    print(f'Classes  : human={sum(y==0)}  script={sum(y==1)}  llm={sum(y==2)}')

    # Check minimum samples per class for CV
    min_samples = min(sum(y==i) for i in range(3) if sum(y==i) > 0)
    if min_samples < 5:
        print(f'\nWarning: smallest class has only {min_samples} samples.')
        print('CV may be unstable. Collect more data for reliable results.')

    print('\n── Ablation Study ──────────────────────────────────')
    print('  (BEI-only replicates reCAPTCHA v3 / existing systems)')
    run_cv(X, y, feature_set='bei')
    print('  (BEI + TIF is your novel contribution)')
    rf_full = run_cv(X, y, feature_set='all')

    print_feature_importance(rf_full)
    print_evaluation(rf_full, X, y)

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    joblib.dump(rf_full, MODEL_OUT)
    print(f'\n✅ Model saved → {MODEL_OUT}')


if __name__ == '__main__':
    main()