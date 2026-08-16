"""
risk_score.py — Converts classifier output into a 0-100 risk score
and determines the action to take.

Score bands:
    0  – 40  → ALLOW          (low risk, likely human)
    41 – 70  → STEP-UP        (medium risk, needs verification)
    71 – 100 → TERMINATE      (high risk, bot detected)
"""


# ── Score band thresholds ────────────────────────────────────────────────────

ALLOW_MAX     = 40
STEPUP_MAX    = 70
TERMINATE_MIN = 71


def compute_risk_score(prediction: str, probabilities: dict) -> int:
    """
    Convert a classifier result into a 0-100 risk score.

    Rules:
    - Script bot  → always high risk (85-100)
    - LLM agent   → always high risk (71-90)
    - Human       → scaled by confidence
                    high confidence human   →  0-20  (very safe)
                    medium confidence human → 21-40  (safe)
                    low confidence human    → 41-60  (needs step-up)
    """
    human_prob  = probabilities.get('human',  0.0)
    script_prob = probabilities.get('script', 0.0)
    llm_prob    = probabilities.get('llm',    0.0)

    if prediction == 'script':
        # Script bots react too fast — terminate immediately
        # Higher script confidence = higher score
        score = 85 + int(script_prob * 15)   # 85–100

    elif prediction == 'llm':
        # LLM agents — terminate, slightly lower than script
        # because there's more ambiguity
        score = 71 + int(llm_prob * 19)      # 71–90

    else:
        # Predicted human — scale by how confident we are
        # High human prob = low risk score
        # Low human prob  = higher risk (step-up)
        score = int((1.0 - human_prob) * 65)  # 0–65

    return max(0, min(100, score))


def get_action(score: int) -> dict:
    """
    Map a risk score to an action.
    Returns action name, label, and description.
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

    Usage:
        result = evaluate_session('llm', {'human': 0.05, 'script': 0.10, 'llm': 0.85})
        # {
        #     'score': 87,
        #     'action': 'terminate',
        #     'label': 'Terminate Session',
        #     'description': '...',
        #     'color': 'red',
        #     'prediction': 'llm',
        #     'probabilities': {...}
        # }
    """
    score  = compute_risk_score(prediction, probabilities)
    action = get_action(score)

    return {
        'score':         score,
        'prediction':    prediction,
        'probabilities': probabilities,
        **action,
    }