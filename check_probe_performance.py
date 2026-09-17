import json
from pathlib import Path
from collections import Counter

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

import sys
sys.path.insert(0, "room3_features")

from pipeline import extract_feature_vector


DATA_DIR = Path("data/sessions")

# Same 7 features used by your final model:
# 0 mouse_curvature_entropy
# 1 typing_rhythm_variance
# 2 scroll_acceleration_mean
# 3 click_hesitation_mean
# 4 mean_probe_reaction_time
# 5 probe_reaction_variance
# 8 cross_layer_decoupling_index
FEATURE_INDICES = [0, 1, 2, 3, 4, 5, 8]

N_SPLITS = 5
RANDOM_STATE = 42


def load_dataset():
    X = []
    y = []
    groups = []
    probe_status = []
    filenames = []

    for file in sorted(DATA_DIR.glob("*.json")):
        try:
            with open(file, "r", encoding="utf-8") as f:
                session = json.load(f)

            label = session.get("label")

            if label not in {"human", "bot", "llm"}:
                continue

            features = extract_feature_vector(session)

            if len(features) != 9:
                continue

            features = np.array(features, dtype=float)

            if not np.all(np.isfinite(features)):
                continue

            # Determine probe condition
            if session.get("probe_enabled") is True:
                status = "Probe ON"
            elif session.get("probe_enabled") is False:
                status = "Probe OFF"
            else:
                status = "Legacy"

            # We only need ON and Legacy for this analysis
            if status not in {"Probe ON", "Legacy"}:
                continue

            experiment_id = session.get("experiment_id")

            if experiment_id:
                group = experiment_id
            else:
                group = file.name

            X.append(features[FEATURE_INDICES])
            y.append(label)
            groups.append(group)
            probe_status.append(status)
            filenames.append(file.name)

        except Exception as e:
            print(f"Skipped {file.name}: {e}")

    return (
        np.array(X),
        np.array(y),
        np.array(groups),
        np.array(probe_status),
    )


def evaluate_subset(X, y, groups, name):

    mask = np.array([True] * len(y))

    X = X[mask]
    y = y[mask]
    groups = groups[mask]

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    counts = Counter(y)

    print(
        f"Sessions: {len(y)} | "
        f"human={counts.get('human', 0)}, "
        f"bot={counts.get('bot', 0)}, "
        f"llm={counts.get('llm', 0)}"
    )

    splitter = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE
    )

    scores = []
    all_true = []
    all_pred = []

    for fold, (train_idx, test_idx) in enumerate(
        splitter.split(X, y, groups),
        start=1
    ):

        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )

        model.fit(
            X[train_idx],
            y[train_idx]
        )

        pred = model.predict(X[test_idx])

        accuracy = accuracy_score(
            y[test_idx],
            pred
        )

        scores.append(accuracy)

        all_true.extend(y[test_idx])
        all_pred.extend(pred)

        print(
            f"Fold {fold}: "
            f"{accuracy * 100:.2f}% "
            f"({len(test_idx)} test sessions)"
        )

    scores = np.array(scores)

    print()
    print(f"Mean accuracy : {scores.mean() * 100:.2f}%")
    print(f"Std deviation : {scores.std() * 100:.2f}%")
    print(f"Min accuracy  : {scores.min() * 100:.2f}%")
    print(f"Max accuracy  : {scores.max() * 100:.2f}%")

    print()
    print("Classification report:")
    print(
        classification_report(
            all_true,
            all_pred,
            labels=["human", "bot", "llm"],
            digits=3
        )
    )

    print("Confusion matrix:")
    print(
        confusion_matrix(
            all_true,
            all_pred,
            labels=["human", "bot", "llm"]
        )
    )


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

X, y, groups, probe_status = load_dataset()

print()
print("DATASET CHECK")
print("-" * 70)

for status in ["Probe ON", "Legacy"]:
    mask = probe_status == status
    counts = Counter(y[mask])

    print(
        f"{status}: {mask.sum()} sessions | "
        f"human={counts.get('human', 0)}, "
        f"bot={counts.get('bot', 0)}, "
        f"llm={counts.get('llm', 0)}"
    )

# Evaluate Probe ON
on_mask = probe_status == "Probe ON"

evaluate_subset(
    X[on_mask],
    y[on_mask],
    groups[on_mask],
    "PROBE ON — 190 SESSIONS"
)

# Evaluate Legacy
legacy_mask = probe_status == "Legacy"

evaluate_subset(
    X[legacy_mask],
    y[legacy_mask],
    groups[legacy_mask],
    "LEGACY — 123 SESSIONS"
)