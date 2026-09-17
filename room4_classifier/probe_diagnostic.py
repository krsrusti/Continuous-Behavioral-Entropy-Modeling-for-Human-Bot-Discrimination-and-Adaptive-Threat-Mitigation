
import json
import glob
import os
import numpy as np


DATA_DIR = r"C:\Users\krsru\OneDrive\Desktop\final project\data\sessions"

classes = {
    "human": [],
    "bot": [],
    "llm": []
}


files = glob.glob(os.path.join(DATA_DIR, "*.json"))


for file_path in files:

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            session = json.load(f)

        label = session.get("label")

        if label not in classes:
            continue

        probes = session.get("probes", [])

        valid_deltas = []

        for probe in probes:

            delta = probe.get("delta")

            if delta is None:
                continue

            if probe.get("abandoned") is True:
                continue

            try:
                delta = float(delta)
            except (TypeError, ValueError):
                continue

            if 50 < delta <= 5000:
                valid_deltas.append(delta)

        classes[label].append(valid_deltas)

    except Exception as e:
        print(f"Skipped {file_path}: {e}")


print("\n" + "=" * 70)
print("PROBE DATASET DIAGNOSTIC")
print("=" * 70)


for label, sessions in classes.items():

    total_sessions = len(sessions)

    sessions_with_probes = sum(
        1 for s in sessions if len(s) > 0
    )

    total_valid_probes = sum(
        len(s) for s in sessions
    )

    all_deltas = [
        delta
        for session in sessions
        for delta in session
    ]

    print(f"\n{label.upper()}")

    print(f"Sessions: {total_sessions}")

    print(
        f"Sessions with valid probes: "
        f"{sessions_with_probes}/{total_sessions}"
    )

    print(
        f"Total valid probes: "
        f"{total_valid_probes}"
    )

    if all_deltas:

        print(
            f"Mean reaction: "
            f"{np.mean(all_deltas):.2f} ms"
        )

        print(
            f"Median reaction: "
            f"{np.median(all_deltas):.2f} ms"
        )

        print(
            f"Min reaction: "
            f"{np.min(all_deltas):.2f} ms"
        )

        print(
            f"Max reaction: "
            f"{np.max(all_deltas):.2f} ms"
        )

    else:

        print("No valid probe reactions.")

print("\n" + "=" * 70)
