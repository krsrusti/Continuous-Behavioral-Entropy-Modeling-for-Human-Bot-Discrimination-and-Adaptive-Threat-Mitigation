"""
evaluate.py — Full classification report + confusion matrix + individual predictions.

Usage:
    python room4_classifier/evaluate.py
"""

import os
import sys
import json
import glob

import numpy as np
import joblib

from sklearn.metrics import classification_report, confusion_matrix


# ─────────────────────────────────────────────────────────────────────────────
# Import feature pipeline
# ─────────────────────────────────────────────────────────────────────────────

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), '..')
)

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), '../room3_features')
)

from pipeline import extract_feature_vector


# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    'saved_models/rf_model.pkl'
)

SESSIONS_DIR = os.path.join(
    os.path.dirname(__file__),
    '../data/sessions'
)


# ─────────────────────────────────────────────────────────────────────────────
# Labels
# ─────────────────────────────────────────────────────────────────────────────

LABEL_MAP = {
    'human': 0,
    'bot': 1,
    'llm': 2
}

LABEL_NAMES = [
    'human',
    'bot',
    'llm'
]


# ─────────────────────────────────────────────────────────────────────────────
# Features used by the saved model
# ─────────────────────────────────────────────────────────────────────────────
#
# pipeline.py creates 12 features.
#
# The saved Random Forest was trained using only these 10 features.
#
# Removed:
#   action_burstiness_score
#   cognitive_hesitation_gap
#
# ─────────────────────────────────────────────────────────────────────────────

MODEL_FEATURE_INDICES = [

    0,   # mouse_curvature_entropy
    1,   # typing_rhythm_variance
    2,   # scroll_acceleration_mean
    3,   # click_hesitation_mean

    4,   # mean_probe_reaction_time
    5,   # probe_reaction_variance
    6,   # median_probe_reaction_time
    7,   # probe_reaction_iqr
    8,   # probe_success_rate

    11   # cross_layer_decoupling_index
]


MODEL_FEATURE_NAMES = [

    'mouse_curvature_entropy',
    'typing_rhythm_variance',
    'scroll_acceleration_mean',
    'click_hesitation_mean',

    'mean_probe_reaction_time',
    'probe_reaction_variance',
    'median_probe_reaction_time',
    'probe_reaction_iqr',
    'probe_success_rate',

    'cross_layer_decoupling_index'
]


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():

    # ─────────────────────────────────────────────────────────────────────────
    # Check model
    # ─────────────────────────────────────────────────────────────────────────

    if not os.path.exists(MODEL_PATH):

        print('Model not found. Run train.py first.')
        return

    model = joblib.load(MODEL_PATH)

    print('Model loaded.')
    print(
        f'Model expects {model.n_features_in_} features.'
    )

    # Make sure our evaluator matches the saved model.

    if model.n_features_in_ != len(MODEL_FEATURE_INDICES):

        print(
            f'ERROR: Model expects '
            f'{model.n_features_in_} features, '
            f'but this evaluator is configured for '
            f'{len(MODEL_FEATURE_INDICES)} features.'
        )

        return


    # ─────────────────────────────────────────────────────────────────────────
    # Find session files
    # ─────────────────────────────────────────────────────────────────────────

    files = [
        f
        for f in glob.glob(
            os.path.join(SESSIONS_DIR, '*.json')
        )
        if os.path.getsize(f) > 100
    ]

    print(
        f'Sessions found: {len(files)}'
    )


    # ─────────────────────────────────────────────────────────────────────────
    # Load dataset
    # ─────────────────────────────────────────────────────────────────────────

    X = []
    y = []
    session_names = []

    for path in files:

        try:

            with open(
                path,
                encoding='utf-8'
            ) as f:

                session = json.load(f)

        except Exception as e:

            print(
                f'Skipping {os.path.basename(path)} '
                f'because it could not be read: {e}'
            )

            continue


        # Get ground-truth label.

        label = session.get('label')

        if label not in LABEL_MAP:

            continue


        # ─────────────────────────────────────────────────────────────────────
        # Extract all 12 features
        # ─────────────────────────────────────────────────────────────────────

        full_vector = extract_feature_vector(
            session
        )


        # Safety check.

        if len(full_vector) != 12:

            print(
                f'Skipping {os.path.basename(path)}: '
                f'expected 12 features, '
                f'got {len(full_vector)}'
            )

            continue


        # ─────────────────────────────────────────────────────────────────────
        # Select the 10 features used by the model
        # ─────────────────────────────────────────────────────────────────────

        model_vector = [

            full_vector[index]
            for index in MODEL_FEATURE_INDICES

        ]


        X.append(model_vector)

        y.append(
            LABEL_MAP[label]
        )

        session_names.append(
            os.path.basename(path)
        )


    # ─────────────────────────────────────────────────────────────────────────
    # Check dataset
    # ─────────────────────────────────────────────────────────────────────────

    if not X:

        print('No labelled sessions found.')
        return


    X = np.array(X)
    y = np.array(y)


    print(
        f'Sessions used: {len(X)}'
    )

    print(
        f'Features used: {X.shape[1]}'
    )


    # ─────────────────────────────────────────────────────────────────────────
    # Display features
    # ─────────────────────────────────────────────────────────────────────────

    print(
        '\nFeatures passed to model:'
    )

    for i, name in enumerate(
        MODEL_FEATURE_NAMES
    ):

        print(
            f'  {i + 1}. {name}'
        )


    # ─────────────────────────────────────────────────────────────────────────
    # Predictions
    # ─────────────────────────────────────────────────────────────────────────

    preds = model.predict(X)


    # ─────────────────────────────────────────────────────────────────────────
    # Convert labels to the same format
    # ─────────────────────────────────────────────────────────────────────────
    #
    # y contains:
    #
    #   0 = human
    #   1 = bot
    #   2 = llm
    #
    # The saved model returns:
    #
    #   'human'
    #   'bot'
    #   'llm'
    #
    # Convert y to strings so both arrays can be compared.
    # ─────────────────────────────────────────────────────────────────────────

    actual_labels = np.array([

        LABEL_NAMES[int(label)]
        for label in y

    ])


    predicted_labels = np.array([

        str(label)
        for label in preds

    ])


    # ─────────────────────────────────────────────────────────────────────────
    # Individual predictions
    # ─────────────────────────────────────────────────────────────────────────

    print(
        '\n── Individual Session Predictions '
        '──────────────────'
    )

    print(
        f'{"Session":>45}  '
        f'{"Actual":>10}  '
        f'{"Predicted":>10}'
    )

    print('-' * 72)


    for session_name, actual, predicted in zip(

        session_names,
        actual_labels,
        predicted_labels

    ):

        print(

            f'{session_name:>45}  '
            f'{actual:>10}  '
            f'{predicted:>10}'

        )


    # ─────────────────────────────────────────────────────────────────────────
    # Classification Report
    # ─────────────────────────────────────────────────────────────────────────

    print(
        '\n── Classification Report '
        '────────────────────────────'
    )


    print(

        classification_report(

            actual_labels,
            predicted_labels,

            labels=LABEL_NAMES,

            target_names=LABEL_NAMES

        )

    )


    # ─────────────────────────────────────────────────────────────────────────
    # Confusion Matrix
    # ─────────────────────────────────────────────────────────────────────────

    print(
        '── Confusion Matrix '
        '────────────────────────────────'
    )


    cm = confusion_matrix(

        actual_labels,
        predicted_labels,

        labels=LABEL_NAMES

    )


    print(

        f'{"":>10}  '
        f'{"human":>8}  '
        f'{"bot":>8}  '
        f'{"llm":>8}'

    )


    for row_label, row in zip(

        LABEL_NAMES,
        cm

    ):

        print(

            f'{row_label:>10}  '
            f'{row[0]:>8}  '
            f'{row[1]:>8}  '
            f'{row[2]:>8}'

        )


    # ─────────────────────────────────────────────────────────────────────────
    # Per-class Accuracy
    # ─────────────────────────────────────────────────────────────────────────

    print(
        '\n── Per-class Accuracy '
        '───────────────────────────────'
    )


    for name in LABEL_NAMES:

        mask = actual_labels == name


        correct = (

            predicted_labels[mask]
            == actual_labels[mask]

        ).sum()


        total = mask.sum()


        if total == 0:

            print(
                f'  {name:8s}: 0/0 (N/A)'
            )

        else:

            print(

                f'  {name:8s}: '
                f'{correct}/{total} '
                f'({correct / total:.1%})'

            )


# ─────────────────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    main()