"""
tif_features.py — Family B: Novel TIF Features (Your Contribution).

1. mean_probe_reaction_time      — average T2-T1 across all completed probes
2. probe_reaction_variance       — variance of probe deltas
3. action_burstiness_score       — Allen-Fano burstiness of inter-action intervals
4. cognitive_hesitation_gap      — mean pause before first keydown per input field
5. cross_layer_decoupling_index  — 1 - |Pearson r| between action rate & probe deltas
"""
import numpy as np
from typing import List, Dict


class TIFExtractor:
    def __init__(self, passive_events: List[dict], probes: List[dict]):
        self.passive = passive_events
        self.probes  = probes

    def _completed_deltas(self) -> List[float]:
        """
        Filter probe deltas:
        - Must be > 50ms   (removes same-tick mutation noise)
        - Must be < 3000ms (removes idle gaps where user walked away)
        """
        return [p['delta'] for p in self.probes
                if p.get('delta') is not None
                and p['delta'] > 50
                and p['delta'] < 3000]

    def _action_timestamps(self) -> List[float]:
        action_types = {'mouse_move', 'keydown', 'click', 'scroll'}
        return sorted(e['ts'] for e in self.passive
                      if e.get('type') in action_types)

    def mean_probe_reaction_time(self) -> float:
        deltas = self._completed_deltas()
        return float(np.mean(deltas)) if deltas else 0.0

    def probe_reaction_variance(self) -> float:
        deltas = self._completed_deltas()
        return float(np.var(deltas)) if len(deltas) > 1 else 0.0

    def action_burstiness_score(self) -> float:
        """Allen-Fano ratio B = (sigma - mu) / (sigma + mu).
        B ~ 0: Poisson/human. B > 0: bursty/bot. B < 0: regular."""
        ts = self._action_timestamps()
        if len(ts) < 2:
            return 0.0
        iai         = np.diff(ts)
        mu, sigma   = np.mean(iai), np.std(iai)
        denominator = sigma + mu
        return float((sigma - mu) / denominator) if denominator != 0 else 0.0

    def cognitive_hesitation_gap(self) -> float:
        focuses  = sorted(
            (e for e in self.passive if e.get('type') == 'focus'),
            key=lambda e: e['ts']
        )
        keydowns = sorted(
            (e for e in self.passive if e.get('type') == 'keydown'),
            key=lambda e: e['ts']
        )
        gaps = []
        for foc in focuses:
            first_kd = next(
                (k for k in keydowns if k['ts'] > foc['ts']), None
            )
            if first_kd:
                gaps.append(first_kd['ts'] - foc['ts'])
        return float(np.mean(gaps)) if gaps else 0.0

    def cross_layer_decoupling_index(self) -> float:
        completed = [p for p in self.probes
                     if p.get('delta') is not None
                     and p['delta'] > 50
                     and p['delta'] < 3000]
        if len(completed) < 3:
            return 0.0
        action_ts   = self._action_timestamps()
        window_ms   = 2000
        local_rates = []
        for p in completed:
            t1    = p['t1']
            count = sum(1 for ts in action_ts
                        if t1 - window_ms <= ts <= t1 + window_ms)
            local_rates.append(count)
        deltas = [p['delta'] for p in completed]
        if np.std(local_rates) == 0 or np.std(deltas) == 0:
            return 0.0
        r = np.corrcoef(local_rates, deltas)[0, 1]
        return float(1.0 - abs(r))

    def extract(self) -> Dict[str, float]:
        return {
            'mean_probe_reaction_time':     self.mean_probe_reaction_time(),
            'probe_reaction_variance':      self.probe_reaction_variance(),
            'action_burstiness_score':      self.action_burstiness_score(),
            'cognitive_hesitation_gap':     self.cognitive_hesitation_gap(),
            'cross_layer_decoupling_index': self.cross_layer_decoupling_index(),
        }