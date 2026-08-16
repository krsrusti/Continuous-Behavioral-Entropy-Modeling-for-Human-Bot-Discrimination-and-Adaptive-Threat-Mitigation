"""
pipeline.py — Orchestrates Family A + B extractors into a flat feature vector.
"""
from extractors.bei_features import BEIExtractor
from extractors.tif_features import TIFExtractor

FEATURE_NAMES = [
    # Family A — BEI (Baseline)
    'mouse_curvature_entropy',
    'typing_rhythm_variance',
    'scroll_acceleration_mean',
    'click_hesitation_mean',
    # Family B — TIF (Novel contribution)
    'mean_probe_reaction_time',
    'probe_reaction_variance',
    'action_burstiness_score',
    'cognitive_hesitation_gap',
    'cross_layer_decoupling_index',
]


def extract_feature_vector(session: dict) -> list:
    """Return a list of 9 floats in FEATURE_NAMES order."""
    passive = session.get('passive_events', [])
    probes  = session.get('probes', [])

    bei = BEIExtractor(passive).extract()
    tif = TIFExtractor(passive, probes).extract()

    return [
        bei['mouse_curvature_entropy'],
        bei['typing_rhythm_variance'],
        bei['scroll_acceleration_mean'],
        bei['click_hesitation_mean'],
        tif['mean_probe_reaction_time'],
        tif['probe_reaction_variance'],
        tif['action_burstiness_score'],
        tif['cognitive_hesitation_gap'],
        tif['cross_layer_decoupling_index'],
    ]