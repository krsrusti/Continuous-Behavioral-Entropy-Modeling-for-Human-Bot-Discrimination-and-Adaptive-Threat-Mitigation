"""
inference_latency.py — Utilities for analysing the Inference Latency Signal.
"""
import numpy as np
from typing import List, Dict


def compute_latency_stats(probes: List[Dict]) -> Dict:
    """Summarise T2-T1 deltas across a session's probe list."""
    deltas = [p['delta'] for p in probes
              if p.get('delta') is not None and p['delta'] > 0]
    if not deltas:
        return {'count': 0, 'mean': None, 'std': None,
                'min': None, 'max': None, 'p95': None}
    arr = np.array(deltas)
    return {
        'count': len(arr),
        'mean':  float(np.mean(arr)),
        'std':   float(np.std(arr)),
        'min':   float(np.min(arr)),
        'max':   float(np.max(arr)),
        'p95':   float(np.percentile(arr, 95)),
    }


def classify_latency_profile(stats: Dict) -> str:
    """Heuristic pre-classifier based on latency stats alone.
    Returns 'human' | 'script' | 'llm' | 'unknown'."""
    if stats['count'] == 0 or stats['mean'] is None:
        return 'unknown'
    mean, std = stats['mean'], stats['std']
    if mean < 50 and std < 10:
        return 'script'
    if mean > 300 and std > 150:
        return 'llm'
    return 'human'