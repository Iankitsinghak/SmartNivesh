def clamp_score(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamp a score between min_val and max_val."""
    return max(min_val, min(value, max_val))

def get_level_from_score(score: float) -> str:
    """
    Maps a 0-100 score to a qualitative level based on constants.
    0-39: Weak
    40-59: Moderate
    60-74: Good
    75-89: Strong
    90-100: Very Strong
    """
    score = clamp_score(score)
    if score < 40:
        return "WEAK"
    elif score < 60:
        return "MODERATE"
    elif score < 75:
        return "GOOD"
    elif score < 90:
        return "STRONG"
    else:
        return "VERY_STRONG"

def get_generic_level(score: float) -> str:
    """
    Maps a 0-100 score to a generic LOW/MEDIUM/HIGH/VERY_HIGH level.
    0-39: LOW
    40-69: MEDIUM
    70-89: HIGH
    90-100: VERY_HIGH
    """
    score = clamp_score(score)
    if score < 40:
        return "LOW"
    elif score < 70:
        return "MEDIUM"
    elif score < 90:
        return "HIGH"
    else:
        return "VERY_HIGH"
