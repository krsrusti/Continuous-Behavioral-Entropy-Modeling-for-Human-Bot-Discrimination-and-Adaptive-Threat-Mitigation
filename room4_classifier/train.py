"""
train.py

Runs only two experiments:

1. TIF ONLY
2. TIF + BEI

Uses StratifiedGroupKFold to prevent experiment-level
data leakage.

Final TIF + BEI model is saved as:

room4_classifier/saved_models/rf_model.pkl
"""

import os
import sys
import json
import pickle
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# PATHS
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# final project/
BASE_DIR = os.path.dirname(CURRENT_DIR)

# final project/data/sessions/
DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
    "sessions"
)

# final project/room4_classifier/saved_models/
MODEL_DIR = os.path.join(
    CURRENT_DIR,
    "saved_models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "rf_model.pkl"
)

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# ============================================================
# IMPORT PIPELINE FROM ROOM 3
# ============================================================

ROOM3_DIR = os.path.join(
    BASE_DIR,
    "room3_features"
)

sys.path.insert(
    0,
    ROOM3_DIR
)

from pipeline import extract_feature_vector


# ============================================================
# FEATURE DEFINITIONS
# ============================================================

# ------------------------------------------------------------
# BEI FEATURES
# ------------------------------------------------------------

BEI_FEATURES = [

    "mouse_curvature_entropy",

    "typing_rhythm_variance",

    "scroll_acceleration_mean",

    "click_hesitation_mean",

]


# ------------------------------------------------------------
# TIF FEATURES
# ------------------------------------------------------------

TIF_FEATURES = [

    "mean_probe_reaction_time",

    "probe_reaction_variance",

    "median_probe_reaction_time",

    "probe_reaction_iqr",

    "probe_success_rate",

    "action_burstiness_score",

    "cognitive_hesitation_gap",

    "cross_layer_decoupling_index",

]


# ------------------------------------------------------------
# ALL FEATURES
# ------------------------------------------------------------

ALL_FEATURES = (
    BEI_FEATURES +
    TIF_FEATURES
)


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset():

    X = []
    y = []
    groups = []

    skipped = 0

    print("=" * 70)
    print("LOADING DATA")
    print("=" * 70)

    # --------------------------------------------------------
    # Check data directory
    # --------------------------------------------------------

    if not os.path.exists(DATA_DIR):

        raise RuntimeError(
            f"Data directory not found:\n"
            f"{DATA_DIR}"
        )

    # --------------------------------------------------------
    # Find JSON files
    # --------------------------------------------------------

    files = [

        f

        for f in os.listdir(DATA_DIR)

        if f.lower().endswith(".json")

    ]

    print(
        f"JSON files found : {len(files)}"
    )

    # ========================================================
    # Process sessions
    # ========================================================

    for filename in files:

        path = os.path.join(
            DATA_DIR,
            filename
        )

        # ----------------------------------------------------
        # Read JSON
        # ----------------------------------------------------

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                session = json.load(f)

        except Exception as e:

            print(
                f"[SKIP] {filename}: {e}"
            )

            skipped += 1

            continue

        # ----------------------------------------------------
        # Get label
        # ----------------------------------------------------

        label = session.get(
            "agent_class"
        )

        if label not in [
            "human",
            "bot",
            "llm"
        ]:

            skipped += 1

            continue

        # ----------------------------------------------------
        # Get experiment group
        # ----------------------------------------------------

        group = session.get(
            "experiment_id"
        )

        if not group:

            group = filename

        # ====================================================
        # Extract 12 features
        # ====================================================

        try:

            feature_vector = (
                extract_feature_vector(
                    session
                )
            )

        except Exception as e:

            print(
                f"[SKIP] Feature extraction failed:"
                f" {filename}"
            )

            print(
                f"       {e}"
            )

            skipped += 1

            continue

        # ----------------------------------------------------
        # Check feature count
        # ----------------------------------------------------

        if len(feature_vector) != len(
            ALL_FEATURES
        ):

            print(
                f"[SKIP] Wrong feature count:"
                f" {filename}"
            )

            print(
                f"       Expected: "
                f"{len(ALL_FEATURES)}"
            )

            print(
                f"       Got: "
                f"{len(feature_vector)}"
            )

            skipped += 1

            continue

        # ----------------------------------------------------
        # Convert values to float
        # ----------------------------------------------------

        values = []

        valid = True

        for value in feature_vector:

            try:

                value = float(value)

            except (
                TypeError,
                ValueError
            ):

                valid = False

                break

            if not np.isfinite(value):

                valid = False

                break

            values.append(value)

        # ----------------------------------------------------
        # Skip invalid session
        # ----------------------------------------------------

        if not valid:

            skipped += 1

            continue

        # ----------------------------------------------------
        # Store
        # ----------------------------------------------------

        X.append(values)

        y.append(label)

        groups.append(group)

    # ========================================================
    # Convert to NumPy
    # ========================================================

    X = np.array(
        X,
        dtype=float
    )

    y = np.array(y)

    groups = np.array(groups)

    # ========================================================
    # Dataset summary
    # ========================================================

    print()

    print(
        f"Usable sessions  : {len(X)}"
    )

    print(
        f"Skipped           : {skipped}"
    )

    print()

    print("Classes:")

    for cls in [
        "human",
        "bot",
        "llm"
    ]:

        print(
            f"  {cls:<7} = "
            f"{np.sum(y == cls)}"
        )

    print()

    print(
        f"Unique groups     : "
        f"{len(np.unique(groups))}"
    )

    return (
        X,
        y,
        groups
    )


# ============================================================
# EVALUATE MODEL
# ============================================================

def evaluate_model(
    X,
    y,
    groups,
    feature_names,
    experiment_name
):

    print()
    print("=" * 70)

    print(
        f"VALIDATION: "
        f"{experiment_name}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Cross-validation
    # --------------------------------------------------------

    cv = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    fold_scores = []

    all_true = []

    all_pred = []

    # ========================================================
    # 5 folds
    # ========================================================

    for fold, (
        train_idx,
        test_idx
    ) in enumerate(
        cv.split(
            X,
            y,
            groups
        ),
        start=1
    ):

        # ----------------------------------------------------
        # Split data
        # ----------------------------------------------------

        X_train = X[
            train_idx
        ]

        X_test = X[
            test_idx
        ]

        y_train = y[
            train_idx
        ]

        y_test = y[
            test_idx
        ]

        # ----------------------------------------------------
        # Check group leakage
        # ----------------------------------------------------

        train_groups = set(
            groups[train_idx]
        )

        test_groups = set(
            groups[test_idx]
        )

        overlap = (
            train_groups
            .intersection(
                test_groups
            )
        )

        if overlap:

            raise RuntimeError(
                f"GROUP LEAKAGE DETECTED "
                f"in fold {fold}: "
                f"{len(overlap)} overlapping groups"
            )

        # ----------------------------------------------------
        # Create model
        # ----------------------------------------------------

        model = RandomForestClassifier(

            n_estimators=200,

            max_depth=None,

            random_state=42,

            n_jobs=-1

        )

        # ----------------------------------------------------
        # Train
        # ----------------------------------------------------

        model.fit(
            X_train,
            y_train
        )

        # ----------------------------------------------------
        # Predict
        # ----------------------------------------------------

        predictions = model.predict(
            X_test
        )

        # ----------------------------------------------------
        # Accuracy
        # ----------------------------------------------------

        accuracy = accuracy_score(
            y_test,
            predictions
        )

        fold_scores.append(
            accuracy
        )

        # ----------------------------------------------------
        # Store predictions
        # ----------------------------------------------------

        all_true.extend(
            y_test
        )

        all_pred.extend(
            predictions
        )

        print(
            f"Fold {fold}: "
            f"{accuracy * 100:.2f}% "
            f"({len(test_idx)} sessions)"
        )

    # ========================================================
    # Accuracy statistics
    # ========================================================

    mean_accuracy = np.mean(
        fold_scores
    )

    std_accuracy = np.std(
        fold_scores
    )

    min_accuracy = min(
        fold_scores
    )

    max_accuracy = max(
        fold_scores
    )

    print()

    print("RESULT")

    print("-" * 70)

    print(
        f"Mean accuracy : "
        f"{mean_accuracy * 100:.2f}%"
    )

    print(
        f"Std deviation : "
        f"{std_accuracy * 100:.2f}%"
    )

    print(
        f"Minimum fold  : "
        f"{min_accuracy * 100:.2f}%"
    )

    print(
        f"Maximum fold  : "
        f"{max_accuracy * 100:.2f}%"
    )

    # ========================================================
    # Classification report
    # ========================================================

    print()

    print(
        "CLASSIFICATION REPORT"
    )

    print("-" * 70)

    print(
        classification_report(

            all_true,

            all_pred,

            labels=[
                "human",
                "bot",
                "llm"
            ],

            digits=3,

            zero_division=0

        )
    )

    # ========================================================
    # Confusion matrix
    # ========================================================

    print(
        "CONFUSION MATRIX"
    )

    print("-" * 70)

    cm = confusion_matrix(

        all_true,

        all_pred,

        labels=[
            "human",
            "bot",
            "llm"
        ]

    )

    print()

    print(
        "              predicted"
    )

    print(
        "             human  bot  llm"
    )

    print(
        f"human       "
        f"{cm[0][0]:5d}"
        f"{cm[0][1]:5d}"
        f"{cm[0][2]:5d}"
    )

    print(
        f"bot         "
        f"{cm[1][0]:5d}"
        f"{cm[1][1]:5d}"
        f"{cm[1][2]:5d}"
    )

    print(
        f"llm         "
        f"{cm[2][0]:5d}"
        f"{cm[2][1]:5d}"
        f"{cm[2][2]:5d}"
    )

    return (
        mean_accuracy,
        std_accuracy
    )


# ============================================================
# TRAIN FINAL MODEL
# ============================================================

def train_final_model(
    X,
    y,
    feature_names
):

    print()
    print("=" * 70)

    print(
        "TRAINING FINAL TIF + BEI MODEL"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Random Forest
    # --------------------------------------------------------

    model = RandomForestClassifier(

        n_estimators=200,

        max_depth=None,

        random_state=42,

        n_jobs=-1

    )

    # --------------------------------------------------------
    # Train on all data
    # --------------------------------------------------------

    model.fit(
        X,
        y
    )

    # ========================================================
    # Feature importance
    # ========================================================

    importances = (
        model.feature_importances_
    )

    importance_pairs = sorted(

        zip(
            feature_names,
            importances
        ),

        key=lambda x: x[1],

        reverse=True

    )

    print()

    print(
        "FEATURE IMPORTANCES"
    )

    print("-" * 70)

    for (
        name,
        importance
    ) in importance_pairs:

        print(
            f"{name:<35} "
            f"{importance:.4f}"
        )

    # ========================================================
    # Save model
    # ========================================================

    model_data = {

        "model": model,

        "features": feature_names,

        "classes": [
            "human",
            "bot",
            "llm"
        ]

    }

    with open(
        MODEL_PATH,
        "wb"
    ) as f:

        pickle.dump(
            model_data,
            f
        )

    print()

    print(
        "Final model saved to:"
    )

    print(
        MODEL_PATH
    )

    return model


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # LOAD DATA
    # ========================================================

    X, y, groups = load_dataset()

    if len(X) == 0:

        raise RuntimeError(
            "No usable sessions found."
        )

    # ========================================================
    # FEATURE INDEXES
    # ========================================================

    bei_indices = [

        ALL_FEATURES.index(
            feature
        )

        for feature in BEI_FEATURES

    ]

    tif_indices = [

        ALL_FEATURES.index(
            feature
        )

        for feature in TIF_FEATURES

    ]

    # ========================================================
    # EXPERIMENT 1
    # TIF ONLY
    # ========================================================

    X_tif = X[
        :,
        tif_indices
    ]

    tif_mean, tif_std = (
        evaluate_model(

            X_tif,

            y,

            groups,

            TIF_FEATURES,

            "TIF ONLY"

        )
    )

    # ========================================================
    # EXPERIMENT 2
    # TIF + BEI
    # ========================================================

    X_tif_bei = X[
        :,
        bei_indices + tif_indices
    ]

    TIF_BEI_FEATURES = (

        BEI_FEATURES +

        TIF_FEATURES

    )

    tif_bei_mean, tif_bei_std = (
        evaluate_model(

            X_tif_bei,

            y,

            groups,

            TIF_BEI_FEATURES,

            "TIF + BEI"

        )
    )

    # ========================================================
    # FINAL COMPARISON
    # ========================================================

    print()

    print("=" * 70)

    print(
        "FINAL COMPARISON"
    )

    print("=" * 70)

    print()

    print(
        f"TIF only :     "
        f"{tif_mean * 100:.2f}% "
        f"± {tif_std * 100:.2f}%"
    )

    print(
        f"TIF + BEI :    "
        f"{tif_bei_mean * 100:.2f}% "
        f"± {tif_bei_std * 100:.2f}%"
    )

    # --------------------------------------------------------
    # Improvement
    # --------------------------------------------------------

    improvement = (

        tif_bei_mean -

        tif_mean

    ) * 100

    print()

    print(
        f"TIF + BEI improvement: "
        f"{improvement:+.2f} "
        f"percentage points"
    )

    # ========================================================
    # TRAIN FINAL MODEL
    # ========================================================

    train_final_model(

        X_tif_bei,

        y,

        TIF_BEI_FEATURES

    )

    # ========================================================
    # DONE
    # ========================================================

    print()

    print("=" * 70)

    print(
        "DONE"
    )

    print("=" * 70)