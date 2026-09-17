
"""
bei_features.py

Behavioral Entropy / Interaction (BEI) feature extractor.

These features use only passive behavioral telemetry.
No actual typed characters are stored or used.

Features:
    1. mouse_curvature_entropy
    2. typing_rhythm_variance
    3. scroll_acceleration_mean
    4. click_hesitation_mean

Important:
    Very large gaps between actions are treated as inactivity rather
    than normal behavioral timing. This prevents a user leaving the
    page idle from dominating the features.
"""

import math
import numpy as np
from typing import List, Dict


class BEIExtractor:

    # Gaps larger than this are considered inactivity.
    MAX_GAP_MS = 5000.0

    # For associating focus -> click / focus -> keydown.
    # We do not want an old focus event from several seconds ago
    # to be paired with a completely unrelated action.
    MAX_FOCUS_GAP_MS = 5000.0

    def __init__(self, passive_events: List[dict]):
        self.events = passive_events or []

    # ---------------------------------------------------------
    # Basic helper
    # ---------------------------------------------------------

    def _filter(self, evt_type: str) -> List[dict]:
        """
        Return events of one type, sorted by timestamp.
        """
        events = [
            e for e in self.events
            if e.get("type") == evt_type
            and e.get("ts") is not None
        ]

        return sorted(events, key=lambda e: e["ts"])

    # ---------------------------------------------------------
    # 1. Mouse curvature entropy
    # ---------------------------------------------------------

    def mouse_curvature_entropy(self) -> float:
        """
        Measures how varied the mouse movement directions are.

        A perfectly straight / highly repetitive movement pattern
        has lower directional entropy.

        More varied movement directions produce higher entropy.

        Important fix:
            Angle differences are normalized to [-pi, pi].
            This prevents the discontinuity around +pi / -pi from
            creating artificially huge turns.
        """

        moves = self._filter("mouse_move")

        if len(moves) < 3:
            return 0.0

        angles = []

        for i in range(1, len(moves) - 1):

            x0 = moves[i - 1].get("x")
            y0 = moves[i - 1].get("y")

            x1 = moves[i].get("x")
            y1 = moves[i].get("y")

            x2 = moves[i + 1].get("x")
            y2 = moves[i + 1].get("y")

            # Skip malformed mouse events.
            if None in (x0, y0, x1, y1, x2, y2):
                continue

            dx1 = x1 - x0
            dy1 = y1 - y0

            dx2 = x2 - x1
            dy2 = y2 - y1

            # Ignore zero-length movements.
            if dx1 == 0 and dy1 == 0:
                continue

            if dx2 == 0 and dy2 == 0:
                continue

            angle1 = math.atan2(dy1, dx1)
            angle2 = math.atan2(dy2, dx2)

            # Change in direction.
            turn = angle2 - angle1

            # Normalize angle to [-pi, pi].
            turn = (turn + math.pi) % (2 * math.pi) - math.pi

            angles.append(turn)

        if not angles:
            return 0.0

        # 36 bins across -pi to +pi.
        hist, _ = np.histogram(
            angles,
            bins=36,
            range=(-math.pi, math.pi)
        )

        total = hist.sum()

        if total == 0:
            return 0.0

        probabilities = hist / total

        # Entropy only considers non-zero probabilities.
        probabilities = probabilities[probabilities > 0]

        return float(
            -np.sum(probabilities * np.log2(probabilities))
        )

    # ---------------------------------------------------------
    # 2. Typing rhythm variance
    # ---------------------------------------------------------

    def typing_rhythm_variance(self) -> float:
        """
        Measures variation in time between consecutive keydown events.

        Important fix:
            Long inactivity periods are not considered typing rhythm.

        Example:

            keydown
            keydown
            keydown
            [user leaves page for 30 seconds]
            keydown

        The 30-second gap should not dominate the variance.

        Therefore only intervals <= MAX_GAP_MS are used.
        """

        keydowns = self._filter("keydown")

        if len(keydowns) < 2:
            return 0.0

        timestamps = [
            float(e["ts"])
            for e in keydowns
        ]

        intervals = np.diff(timestamps)

        # Remove inactivity gaps.
        intervals = intervals[
            (intervals > 0) &
            (intervals <= self.MAX_GAP_MS)
        ]

        if len(intervals) == 0:
            return 0.0

        return float(np.var(intervals))

    # ---------------------------------------------------------
    # 3. Scroll acceleration
    # ---------------------------------------------------------

    def scroll_acceleration_mean(self) -> float:
        """
        Estimates mean absolute scroll acceleration.

        Instead of simply comparing:

            dy2 - dy1

        we account for the time between scroll events:

            velocity = dy / dt

            acceleration = (velocity2 - velocity1) / dt

        This makes the feature more meaningful because the same
        scroll-distance change over 10 ms is different from the
        same change over 500 ms.

        Very large inactivity gaps are ignored.
        """

        scrolls = self._filter("scroll")

        if len(scrolls) < 3:
            return 0.0

        velocities = []
        velocity_times = []

        for i in range(1, len(scrolls)):

            previous = scrolls[i - 1]
            current = scrolls[i]

            try:
                t1 = float(previous["ts"])
                t2 = float(current["ts"])
                dy = float(current.get("dy", 0))
            except (TypeError, ValueError):
                continue

            dt = t2 - t1

            # Ignore invalid or very large gaps.
            if dt <= 0 or dt > self.MAX_GAP_MS:
                continue

            velocity = dy / dt

            velocities.append(velocity)
            velocity_times.append(t2)

        if len(velocities) < 2:
            return 0.0

        accelerations = []

        for i in range(1, len(velocities)):

            dt = velocity_times[i] - velocity_times[i - 1]

            if dt <= 0 or dt > self.MAX_GAP_MS:
                continue

            acceleration = (
                velocities[i] - velocities[i - 1]
            ) / dt

            accelerations.append(abs(acceleration))

        if not accelerations:
            return 0.0

        return float(np.mean(accelerations))

    # ---------------------------------------------------------
    # Helper: find recent focus
    # ---------------------------------------------------------

    def _find_recent_focus(
        self,
        timestamp: float
    ):
        """
        Find the most recent focus event before an action.

        Only accept it if the focus is reasonably close to the
        action. This prevents an unrelated old focus event from
        being used.
        """

        focuses = self._filter("focus")

        if not focuses:
            return None

        previous_focus = None

        for focus in focuses:

            focus_ts = float(focus["ts"])

            if focus_ts >= timestamp:
                break

            previous_focus = focus

        if previous_focus is None:
            return None

        gap = timestamp - float(previous_focus["ts"])

        if gap < 0 or gap > self.MAX_FOCUS_GAP_MS:
            return None

        return previous_focus

    # ---------------------------------------------------------
    # 4. Click hesitation
    # ---------------------------------------------------------

    def click_hesitation_mean(self) -> float:
        """
        Measures the average time between a recent focus event and
        the user's click.

        Instead of pairing every click with ANY previous focus,
        we only use a nearby focus event.

        This prevents unrelated long gaps from contaminating the
        feature.
        """

        clicks = self._filter("click")

        if not clicks:
            return 0.0

        gaps = []

        for click in clicks:

            try:
                click_ts = float(click["ts"])
            except (TypeError, ValueError):
                continue

            focus = self._find_recent_focus(click_ts)

            if focus is None:
                continue

            gap = click_ts - float(focus["ts"])

            if 0 <= gap <= self.MAX_FOCUS_GAP_MS:
                gaps.append(gap)

        if not gaps:
            return 0.0

        return float(np.mean(gaps))

    # ---------------------------------------------------------
    # Final feature extraction
    # ---------------------------------------------------------

    def extract(self) -> Dict[str, float]:
        """
        Extract all BEI features for one session.
        """

        return {
            "mouse_curvature_entropy":
                self.mouse_curvature_entropy(),

            "typing_rhythm_variance":
                self.typing_rhythm_variance(),

            "scroll_acceleration_mean":
                self.scroll_acceleration_mean(),

            "click_hesitation_mean":
                self.click_hesitation_mean(),
        }
