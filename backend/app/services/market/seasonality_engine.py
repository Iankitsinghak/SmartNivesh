from app.schemas.business import BusinessCategory
from app.schemas.market import SeasonalityResult

def analyze_seasonality(category: BusinessCategory) -> SeasonalityResult:
    profile = category.seasonality_profile
    peak_periods = profile.get("peak", [])
    low_periods = profile.get("low", [])
    
    # Deterministic scoring: if it has peaks, it has seasonality
    # High number of low periods means lower overall score (more risk)
    score = 100.0 - (len(low_periods) * 20.0)
    score = max(0.0, min(score, 100.0))
    
    if score >= 80:
        level = "STABLE"
    elif score >= 50:
        level = "MODERATELY_SEASONAL"
    else:
        level = "HIGHLY_SEASONAL"
        
    risk_note = "High dependency on specific seasons." if level == "HIGHLY_SEASONAL" else None
    
    return SeasonalityResult(
        seasonality_score=score,
        seasonality_level=level,
        peak_periods=peak_periods,
        low_periods=low_periods,
        risk_note=risk_note
    )
