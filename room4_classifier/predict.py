"""
predict.py — Classify a single session JSON from the command line.

Usage:
    python room4_classifier/predict.py path/to/session.json
    python room4_classifier/predict.py path/to/session.json --verbose
"""
import os, sys, json, argparse
import numpy as np
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../room3_features'))

from pipeline               import extract_feature_vector, FEATURE_NAMES
from calculators.risk_score import evaluate_session, score_band

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'saved_models/rf_model.pkl')
LABEL_MAP  = {0: 'human', 1: 'bot', 2: 'llm'}


# ── Core prediction function ──────────────────────────────────────────────────

def predict_session(session: dict) -> dict:
    """
    Classify a single session and return full result.

    Args:
        session: session dict with passive_events and probes

    Returns:
        {
            prediction, confidence, probabilities,
            score, band, action, label,
            feature_vector, probe_stats
        }
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f'Model not found at {MODEL_PATH}. Run train.py first.'
        )

    model    = joblib.load(MODEL_PATH)
    features = extract_feature_vector(session)
    X        = np.array(features).reshape(1, -1)
    pred     = model.predict(X)[0]
    proba    = model.predict_proba(X)[0]

    prediction    = LABEL_MAP[pred]
    probabilities = {
        'human':  float(proba[0]),
        'bot': float(proba[1]),
        'llm':    float(proba[2]),
    }

    # Risk score
    risk = evaluate_session(prediction, probabilities)

    # Probe stats
    probes = session.get('probes', [])
    deltas = [p['delta'] for p in probes
              if p.get('delta') and p['delta'] > 50 and p['delta'] < 3000]

    probe_stats = {
        'total_probes':   len(probes),
        'valid_deltas':   len(deltas),
        'mean_delta_ms':  round(float(np.mean(deltas)), 1)  if deltas else None,
        'min_delta_ms':   round(float(np.min(deltas)), 1)   if deltas else None,
        'max_delta_ms':   round(float(np.max(deltas)), 1)   if deltas else None,
        'std_delta_ms':   round(float(np.std(deltas)), 1)   if deltas else None,
    }

    return {
        'session_id':     session.get('session_id', '—'),
        'prediction':     prediction,
        'confidence':     float(proba[pred]),
        'probabilities':  probabilities,
        'score':          risk['score'],
        'band':           score_band(risk['score']),
        'action':         risk['action'],
        'label':          risk['label'],
        'description':    risk['description'],
        'feature_vector': dict(zip(FEATURE_NAMES, [round(f, 4) for f in features])),
        'probe_stats':    probe_stats,
    }


# ── Print functions ───────────────────────────────────────────────────────────

def print_result(result: dict, verbose: bool = False):
    action_colors = {
        'allow':     '✅',
        'stepup':    '⚠️',
        'terminate': '🚫',
    }
    icon = action_colors.get(result['action'], '—')

    print(f'\n── TIF Prediction ───────────────────────────────────')
    print(f'  Session    : {str(result["session_id"])[:24]}')
    print(f'  Prediction : {result["prediction"].upper()}')
    print(f'  Confidence : {result["confidence"]:.1%}')
    print(f'  Risk Score : {result["score"]} / 100  ({result["band"].upper()})')
    print(f'  Action     : {icon}  {result["label"]}')

    print(f'\n── Probabilities ────────────────────────────────────')
    for cls, prob in result['probabilities'].items():
        bar = '█' * int(prob * 30)
        print(f'  {cls:8s}: {prob:.3f}  {bar}')

    print(f'\n── Probe Stats ──────────────────────────────────────')
    ps = result['probe_stats']
    print(f'  Total probes  : {ps["total_probes"]}')
    print(f'  Valid deltas  : {ps["valid_deltas"]}')
    if ps['mean_delta_ms'] is not None:
        print(f'  Mean delta    : {ps["mean_delta_ms"]} ms')
        print(f'  Min  delta    : {ps["min_delta_ms"]} ms')
        print(f'  Max  delta    : {ps["max_delta_ms"]} ms')
        print(f'  Std  delta    : {ps["std_delta_ms"]} ms')

        # Show what class this mean delta suggests
        mean = ps['mean_delta_ms']
        if mean < 80:
            hint = 'BOT-LIKE (too fast)'
        elif mean < 700:
            hint = 'HUMAN-LIKE (normal range)'
        else:
            hint = 'LLM-LIKE (inference overhead)'
        print(f'  Profile       : {hint}')
    else:
        print(f'  No valid probe deltas found')

    if verbose:
        print(f'\n── Feature Vector ───────────────────────────────────')
        bei_features = ['mouse_curvature_entropy', 'typing_rhythm_variance',
                        'scroll_acceleration_mean', 'click_hesitation_mean']
        tif_features = ['mean_probe_reaction_time', 'probe_reaction_variance',
                        'action_burstiness_score', 'cognitive_hesitation_gap',
                        'cross_layer_decoupling_index']

        print('  Family A — BEI (Baseline):')
        for name in bei_features:
            val = result['feature_vector'].get(name, 0)
            print(f'    {name:35s}: {val:>10.4f}')

        print('  Family B — TIF (Novel):')
        for name in tif_features:
            val = result['feature_vector'].get(name, 0)
            print(f'    {name:35s}: {val:>10.4f}')


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='TIF Session Classifier')
    parser.add_argument('session_file', help='Path to session JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show full feature vector breakdown')
    args = parser.parse_args()

    if not os.path.exists(args.session_file):
        print(f'Error: file not found — {args.session_file}')
        sys.exit(1)

    with open(args.session_file) as f:
        session = json.load(f)

    try:
        result = predict_session(session)
        print_result(result, verbose=args.verbose)
    except FileNotFoundError as e:
        print(f'Error: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'Prediction failed: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()