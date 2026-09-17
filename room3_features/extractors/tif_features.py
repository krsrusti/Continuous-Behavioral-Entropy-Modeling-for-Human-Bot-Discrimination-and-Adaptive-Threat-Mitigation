"""
tif_features.py

TIF (Temporal Inference Fingerprinting) feature extractor.

Uses:
    - passive behavioral telemetry
    - active micro-probe telemetry

Goal:
    Capture temporal / reaction characteristics that may help
    distinguish humans, bots/scripts, and LLM agents.

TIF FEATURES:
    1. mean_probe_reaction_time
    2. probe_reaction_variance
    3. median_probe_reaction_time
    4. probe_reaction_iqr
    5. probe_success_rate
    6. action_burstiness_score
    7. cognitive_hesitation_gap
    8. cross_layer_decoupling_index

Important:
    - Abandoned probes are NOT treated as 0 ms reactions.
    - Large inactivity gaps are excluded from behavioral timing.
    - Valid probe responses are allowed up to the probe timeout.
    - Missing measurements remain represented as 0.0.
"""

import numpy as np
from typing import List, Dict


class TIFExtractor:

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    MAX_PROBE_REACTION_MS = 5000.0
    MIN_PROBE_REACTION_MS = 50.0

    MAX_ACTION_GAP_MS = 5000.0

    DECOUPLING_WINDOW_MS = 2000.0

    # ---------------------------------------------------------
    # Constructor
    # ---------------------------------------------------------

    def __init__(
        self,
        passive_events: List[dict],
        probes: List[dict]
    ):
        self.passive = passive_events or []
        self.probes = probes or []

    # ---------------------------------------------------------
    # Helper: completed probe deltas
    # ---------------------------------------------------------

    def _completed_deltas(self) -> List[float]:
        """
        Return valid reaction times from successfully completed probes.

        Valid probe:
            - delta exists
            - delta is numeric
            - delta > 50 ms
            - delta <= 5000 ms
            - not explicitly abandoned
        """

        deltas = []

        for probe in self.probes:

            delta = probe.get("delta")

            if delta is None:
                continue

            if probe.get("abandoned") is True:
                continue

            try:
                delta = float(delta)
            except (TypeError, ValueError):
                continue

            if delta <= self.MIN_PROBE_REACTION_MS:
                continue

            if delta > self.MAX_PROBE_REACTION_MS:
                continue

            deltas.append(delta)

        return deltas

    # ---------------------------------------------------------
    # Helper: action timestamps
    # ---------------------------------------------------------

    def _action_timestamps(self) -> List[float]:
        """
        Return timestamps for meaningful passive actions.
        """

        action_types = {
            "mouse_move",
            "keydown",
            "click",
            "scroll"
        }

        timestamps = []

        for event in self.passive:

            if event.get("type") not in action_types:
                continue

            ts = event.get("ts")

            if ts is None:
                continue

            try:
                timestamps.append(float(ts))
            except (TypeError, ValueError):
                continue

        return sorted(timestamps)

    # ---------------------------------------------------------
    # 1. Mean probe reaction time
    # ---------------------------------------------------------

    def mean_probe_reaction_time(self) -> float:

        deltas = self._completed_deltas()

        if not deltas:
            return 0.0

        return float(np.mean(deltas))

    # ---------------------------------------------------------
    # 2. Probe reaction variance
    # ---------------------------------------------------------

    def probe_reaction_variance(self) -> float:

        deltas = self._completed_deltas()

        if len(deltas) < 2:
            return 0.0

        return float(np.var(deltas))

    # ---------------------------------------------------------
    # 3. Median probe reaction time
    # ---------------------------------------------------------

    def median_probe_reaction_time(self) -> float:
        """
        Median probe reaction time.

        More robust than the mean when a session contains
        one or two unusually slow responses.
        """

        deltas = self._completed_deltas()

        if not deltas:
            return 0.0

        return float(np.median(deltas))

    # ---------------------------------------------------------
    # 4. Probe reaction IQR
    # ---------------------------------------------------------

    def probe_reaction_iqr(self) -> float:
        """
        Interquartile range of probe reaction times.

        IQR = Q3 - Q1

        This measures the spread of the middle 50% of
        reaction times and is less sensitive to extreme values.
        """

        deltas = self._completed_deltas()

        if len(deltas) < 2:
            return 0.0

        q1 = np.percentile(deltas, 25)
        q3 = np.percentile(deltas, 75)

        return float(q3 - q1)

    # ---------------------------------------------------------
    # 5. Probe success rate
    # ---------------------------------------------------------

    def probe_success_rate(self) -> float:
        """
        Ratio of successfully completed probes to total probes.

        Successful probe:
            valid reaction delta exists and is within the
            accepted reaction-time range.

        Abandoned or invalid probes count as unsuccessful.
        """

        total_probes = len(self.probes)

        if total_probes == 0:
            return 0.0

        successful = len(self._completed_deltas())

        return float(successful / total_probes)

    # ---------------------------------------------------------
    # 6. Action burstiness
    # ---------------------------------------------------------

    def action_burstiness_score(self) -> float:
        """
        Measures whether actions happen in bursts or at a
        relatively regular pace.

        Formula:

            B = (sigma - mu) / (sigma + mu)
        """

        timestamps = self._action_timestamps()

        if len(timestamps) < 2:
            return 0.0

        intervals = np.diff(timestamps)

        intervals = intervals[
            (intervals > 0) &
            (intervals <= self.MAX_ACTION_GAP_MS)
        ]

        if len(intervals) == 0:
            return 0.0

        mean_interval = float(np.mean(intervals))
        std_interval = float(np.std(intervals))

        denominator = std_interval + mean_interval

        if denominator == 0:
            return 0.0

        return float(
            (std_interval - mean_interval) / denominator
        )

    # ---------------------------------------------------------
    # 7. Cognitive hesitation gap
    # ---------------------------------------------------------

    def cognitive_hesitation_gap(self) -> float:
        """
        Measures the time between a focus event and the next
        meaningful keydown.
        """

        focuses = sorted(
            [
                e for e in self.passive
                if e.get("type") == "focus"
                and e.get("ts") is not None
            ],
            key=lambda e: e["ts"]
        )

        keydowns = sorted(
            [
                e for e in self.passive
                if e.get("type") == "keydown"
                and e.get("ts") is not None
            ],
            key=lambda e: e["ts"]
        )

        if not focuses or not keydowns:
            return 0.0

        gaps = []

        key_index = 0

        for focus in focuses:

            try:
                focus_ts = float(focus["ts"])
            except (TypeError, ValueError):
                continue

            while (
                key_index < len(keydowns)
                and float(keydowns[key_index]["ts"]) <= focus_ts
            ):
                key_index += 1

            if key_index >= len(keydowns):
                break

            try:
                keydown_ts = float(
                    keydowns[key_index]["ts"]
                )
            except (TypeError, ValueError):
                key_index += 1
                continue

            gap = keydown_ts - focus_ts

            if gap <= 0 or gap > self.MAX_ACTION_GAP_MS:
                continue

            gaps.append(gap)

            key_index += 1

        if not gaps:
            return 0.0

        return float(np.mean(gaps))

    # ---------------------------------------------------------
    # 8. Cross-layer decoupling index
    # ---------------------------------------------------------

    def cross_layer_decoupling_index(self) -> float:
        """
        Measures the relationship between probe reaction time
        and surrounding behavioral activity.
        """

        completed_probes = []

        for probe in self.probes:

            delta = probe.get("delta")
            t1 = probe.get("t1")

            if delta is None or t1 is None:
                continue

            if probe.get("abandoned") is True:
                continue

            try:
                delta = float(delta)
                t1 = float(t1)
            except (TypeError, ValueError):
                continue

            if delta <= self.MIN_PROBE_REACTION_MS:
                continue

            if delta > self.MAX_PROBE_REACTION_MS:
                continue

            completed_probes.append(
                {
                    "t1": t1,
                    "delta": delta
                }
            )

        if len(completed_probes) < 3:
            return 0.0

        action_timestamps = self._action_timestamps()

        if not action_timestamps:
            return 0.0

        local_activity = []
        reaction_times = []

        for probe in completed_probes:

            t1 = probe["t1"]
            delta = probe["delta"]

            window_start = (
                t1 - self.DECOUPLING_WINDOW_MS
            )

            window_end = (
                t1 + self.DECOUPLING_WINDOW_MS
            )

            count = sum(
                1
                for ts in action_timestamps
                if window_start <= ts <= window_end
            )

            local_activity.append(count)
            reaction_times.append(delta)

        if np.std(local_activity) == 0:
            return 0.0

        if np.std(reaction_times) == 0:
            return 0.0

        correlation_matrix = np.corrcoef(
            local_activity,
            reaction_times
        )

        correlation = correlation_matrix[0, 1]

        if not np.isfinite(correlation):
            return 0.0

        return float(
            1.0 - abs(correlation)
        )

    # ---------------------------------------------------------
    # Final feature extraction
    # ---------------------------------------------------------

    def extract(self) -> Dict[str, float]:
        """
        Extract all TIF features for one session.
        """

        return {

            "mean_probe_reaction_time":
                self.mean_probe_reaction_time(),

            "probe_reaction_variance":
                self.probe_reaction_variance(),

            "median_probe_reaction_time":
                self.median_probe_reaction_time(),

            "probe_reaction_iqr":
                self.probe_reaction_iqr(),

            "probe_success_rate":
                self.probe_success_rate(),

            "action_burstiness_score":
                self.action_burstiness_score(),

            "cognitive_hesitation_gap":
                self.cognitive_hesitation_gap(),

            "cross_layer_decoupling_index":
                self.cross_layer_decoupling_index(),
        }