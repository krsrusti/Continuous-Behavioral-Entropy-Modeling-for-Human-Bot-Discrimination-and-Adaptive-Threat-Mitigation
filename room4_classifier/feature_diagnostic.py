
import json
import glob
import os

import numpy as np
import pandas as pd

import sys

sys.path.append(
    r"C:\Users\krsru\OneDrive\Desktop\final project\room3_features"
)

from pipeline import extract_feature_vector, FEATURE_NAMES


DATA_DIR = r"C:\Users\krsru\OneDrive\Desktop\final project\data\sessions"


def load_dataset():
    rows = []

    files = glob.glob(os.path.join(DATA_DIR, "*.json"))

    for file_path in files:

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                session = json.load(f)

            label = session.get("label")

            if label not in {"human", "bot", "llm"}:
                continue

            features = extract_feature_vector(session)

            row = {
                "label": label
            }

            for name, value in zip(FEATURE_NAMES, features):
                row[name] = value

            rows.append(row)

        except Exception as e:
            print(f"Skipped {file_path}: {e}")

    return pd.DataFrame(rows)


def main():

    print("\nLoading dataset ...")

    df = load_dataset()

    print(f"\nSessions used: {len(df)}")

    print("\nClass counts:")
    print(df["label"].value_counts())

    print("\n" + "=" * 80)
    print("FEATURE MEANS BY CLASS")
    print("=" * 80)

    means = df.groupby("label")[FEATURE_NAMES].mean()

    print(means.to_string(float_format=lambda x: f"{x:.4f}"))

    print("\n" + "=" * 80)
    print("FEATURE MEDIANS BY CLASS")
    print("=" * 80)

    medians = df.groupby("label")[FEATURE_NAMES].median()

    print(medians.to_string(float_format=lambda x: f"{x:.4f}"))

    print("\n" + "=" * 80)
    print("FEATURE STANDARD DEVIATION BY CLASS")
    print("=" * 80)

    stds = df.groupby("label")[FEATURE_NAMES].std()

    print(stds.to_string(float_format=lambda x: f"{x:.4f}"))

    print("\n" + "=" * 80)
    print("MIN / MAX BY CLASS")
    print("=" * 80)

    for feature in FEATURE_NAMES:

        print(f"\n--- {feature} ---")

        for label in ["human", "bot", "llm"]:

            values = df.loc[
                df["label"] == label,
                feature
            ].dropna()

            if len(values) == 0:
                continue

            print(
                f"{label:6s}: "
                f"min={values.min():.4f}, "
                f"max={values.max():.4f}, "
                f"mean={values.mean():.4f}"
            )

    print("\n" + "=" * 80)
    print("MISSING / ZERO VALUES")
    print("=" * 80)

    for feature in FEATURE_NAMES:

        zero_count = (
            df[feature] == 0
        ).sum()

        print(
            f"{feature:35s}: "
            f"{zero_count}/{len(df)} "
            f"({zero_count / len(df) * 100:.1f}%) zero"
        )


if __name__ == "__main__":
    main()
