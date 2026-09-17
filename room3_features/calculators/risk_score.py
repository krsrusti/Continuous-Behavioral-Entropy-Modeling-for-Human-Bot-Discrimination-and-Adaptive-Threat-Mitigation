"""
risk_score.py — Converts classifier output into a 0-100 risk score
and determines the action to take.

Score bands:
    0  – 40  → ALLOW          (low risk, likely human)
    41 – 70  → STEP-UP        (medium risk, needs verification)
    71 – 100 → TERMINATE      (high risk, bot detected)

General Formula:
    Risk Score = Base Score + (Confidence × Range)

    Class    Base   Confidence          Range   Result
    ------   ----   -----------------   -----   -------
    Script   85     script_probability  15      85–100
    LLM      71     llm_probability     19      71–90
    Human    0      1 - human_prob      65      0–65
"""


# ── Score band thresholds ─────────────────────────────────────────────────────

ALLOW_MAX     = 40
STEPUP_MAX    = 70
TERMINATE_MIN = 71


# ── Core functions ────────────────────────────────────────────────────────────

def compute_risk_score(prediction: str, probabilities: dict) -> int:
    """
    Convert classifier output into a 0-100 risk score.

    Args:
        prediction:    'human' | 'bot' | 'llm'
        probabilities: {'human': 0.9, 'bot': 0.05, 'llm': 0.05}

    Returns:
        Integer risk score 0-100
    """
    human_prob  = probabilities.get('human',  0.0)
    script_prob = probabilities.get('bot', 0.0)
    llm_prob    = probabilities.get('llm',    0.0)

    if prediction == 'bot':
        # Script bots are most dangerous — always terminate
        # Base 85 ensures minimum score is above terminate threshold
        # Range 15 scales up to 100 with confidence
        score = 85 + int(script_prob * 15)      # 85–100

    elif prediction == 'llm':
        # LLM agents — always terminate
        # Base 71 ensures minimum score is above terminate threshold
        # Range 19 scales up to 90 with confidence
        score = 71 + int(llm_prob * 19)         # 71–90

    else:
        # Human — scored by how UNconfident the model is
        # High human confidence → score near 0 (safe)
        # Low human confidence  → score up to 65 (step-up zone)
        score = int((1.0 - human_prob) * 65)    # 0–65

    return max(0, min(100, score))


def get_action(score: int) -> dict:
    """
    Map a risk score to an action.

    Returns:
        dict with action, label, description, color
    """
    if score <= ALLOW_MAX:
        return {
            'action':      'allow',
            'label':       'Allow Access',
            'description': 'Low risk — session cleared.',
            'color':       'green',
        }
    elif score <= STEPUP_MAX:
        return {
            'action':      'stepup',
            'label':       'Step-up Verification',
            'description': 'Medium risk — require CAPTCHA or OTP.',
            'color':       'yellow',
        }
    else:
        return {
            'action':      'terminate',
            'label':       'Terminate Session',
            'description': 'High risk — bot detected, block session.',
            'color':       'red',
        }


def evaluate_session(prediction: str, probabilities: dict) -> dict:
    """
    Full evaluation — takes classifier output and returns
    score + action in one call.

    Args:
        prediction:    'human' | 'bot' | 'llm'
        probabilities: {'human': float, 'bot': float, 'llm': float}

    Returns:
        {
            'score':         int,
            'action':        'allow' | 'stepup' | 'terminate',
            'label':         str,
            'description':   str,
            'color':         str,
            'prediction':    str,
            'probabilities': dict,
        }

    Example:
        result = evaluate_session(
            'llm',
            {'human': 0.05, 'bot': 0.10, 'llm': 0.85}
        )
        # result['score']  → 87
        # result['action'] → 'terminate'
    """
    score  = compute_risk_score(prediction, probabilities)
    action = get_action(score)

    return {
        'score':         score,
        'prediction':    prediction,
        'probabilities': probabilities,
        **action,
    }


# ── Convenience functions ─────────────────────────────────────────────────────

def is_bot(prediction: str) -> bool:
    """Returns True if prediction is a bot class."""
    return prediction in ('bot', 'llm')


def score_band(score: int) -> str:
    """Returns the band name for a given score."""
    if score <= ALLOW_MAX:
        return 'low'
    elif score <= STEPUP_MAX:
        return 'medium'
    else:
        return 'high'