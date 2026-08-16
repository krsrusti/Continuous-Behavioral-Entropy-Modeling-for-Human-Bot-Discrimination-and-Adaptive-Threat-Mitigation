"""
collect_dataset.py
Extract features from all labelled sessions and save to data/features/features.csv.

Usage:
    python scripts/collect_dataset.py
"""
import os, sys, json, glob
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../room3_features'))
from pipeline import extract_feature_vector, FEATURE_NAMES

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), '../data/sessions')
OUT_CSV      = os.path.join(os.path.dirname(__file__), '../data/features/features.csv')


def main():
    files = [f for f in glob.glob(os.path.join(SESSIONS_DIR, '*.json'))
             if os.path.getsize(f) > 100]

    if not files:
        print('No session files found. Run generate_synthetic_sessions.py first.')
        return

    rows = []
    for path in files:
        with open(path) as f:
            session = json.load(f)
        label    = session.get('label', 'unknown')
        features = extract_feature_vector(session)
        rows.append({
            'session_id': session.get('session_id', os.path.basename(path)),
            'label':      label,
            'page_type':  session.get('page_type', 'unknown'),
            **dict(zip(FEATURE_NAMES, features))
        })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    print(f'Saved {len(df)} rows → {OUT_CSV}')
    print(f'\nLabel distribution:')
    print(df['label'].value_counts().to_string())
    print(f'\nFeature summary:')
    print(df[FEATURE_NAMES].describe().round(2).to_string())


if __name__ == '__main__':
    main()