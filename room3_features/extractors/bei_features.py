"""
bei_features.py — Family A: Traditional BEI Features (Baseline).

1. mouse_curvature_entropy   — Shannon entropy over trajectory angle changes
2. typing_rhythm_variance    — variance of inter-keypress intervals (ms)
3. scroll_acceleration_mean  — mean absolute derivative of scroll dy values
4. click_hesitation_mean     — mean delta between focusin and first click (ms)
"""
import math
import numpy as np
from typing import List, Dict


class BEIExtractor:
    def __init__(self, passive_events: List[dict]):
        self.events = passive_events

    def _filter(self, evt_type: str) -> List[dict]:
        return [e for e in self.events if e.get('type') == evt_type]

    def mouse_curvature_entropy(self) -> float:
        moves = self._filter('mouse_move')
        if len(moves) < 3:
            return 0.0
        angles = []
        for i in range(1, len(moves) - 1):
            dx1 = moves[i]['x']   - moves[i-1]['x']
            dy1 = moves[i]['y']   - moves[i-1]['y']
            dx2 = moves[i+1]['x'] - moves[i]['x']
            dy2 = moves[i+1]['y'] - moves[i]['y']
            angles.append(math.atan2(dy2, dx2) - math.atan2(dy1, dx1))
        hist, _ = np.histogram(angles, bins=36, range=(-math.pi, math.pi))
        prob    = hist / hist.sum() if hist.sum() > 0 else hist
        prob    = prob[prob > 0]
        return float(-np.sum(prob * np.log2(prob)))

    def typing_rhythm_variance(self) -> float:
        keydowns = self._filter('keydown')
        if len(keydowns) < 2:
            return 0.0
        ts = [e['ts'] for e in keydowns]
        return float(np.var(np.diff(ts)))

    def scroll_acceleration_mean(self) -> float:
        scrolls = self._filter('scroll')
        if len(scrolls) < 2:
            return 0.0
        dy_vals = [e.get('dy', 0) for e in scrolls]
        return float(np.mean(np.abs(np.diff(dy_vals))))

    def click_hesitation_mean(self) -> float:
        focuses = {e['ts']: e for e in self._filter('focus')}
        clicks  = self._filter('click')
        gaps = []
        for click in clicks:
            prior = [ts for ts in focuses if ts < click['ts']]
            if prior:
                gaps.append(click['ts'] - max(prior))
        return float(np.mean(gaps)) if gaps else 0.0

    def extract(self) -> Dict[str, float]:
        return {
            'mouse_curvature_entropy':  self.mouse_curvature_entropy(),
            'typing_rhythm_variance':   self.typing_rhythm_variance(),
            'scroll_acceleration_mean': self.scroll_acceleration_mean(),
            'click_hesitation_mean':    self.click_hesitation_mean(),
        }