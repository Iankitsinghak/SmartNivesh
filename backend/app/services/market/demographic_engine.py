import json
from typing import Optional, Dict, Any
from app.schemas.demographic import Demographics
from app.schemas.business import BusinessCategory
from app.core.enums import ConfidenceLevel
from app.utils.normalization import clamp_score
from app.core.database import SessionLocal
from app.models.demographic import DemographicRecord

def get_demographics(location_id: str) -> Optional[Demographics]:
    db = SessionLocal()
    try:
        records = db.query(DemographicRecord).filter(DemographicRecord.location_id == location_id).all()
        if records:
            data = {"location_id": location_id}
            for r in records:
                data[r.indicator] = r.value
            return Demographics(**data)
    except Exception:
        pass
    finally:
        db.close()
    return None

def analyze_demographics(demographics: Demographics, category: BusinessCategory) -> Dict[str, Any]:

    """
    Matches demographics against the target_segments defined in BusinessCategory.
    Calculates a demographic_fit score (0-100).
    """
    if not category.target_segments or not demographics:
        return {
            "demographic_fit": 50.0, # Neutral if no data
            "confidence": ConfidenceLevel.LOW,
            "signals": {}
        }

    total_score = 0.0
    max_possible = 0.0
    signals = {}

    demo_dict = demographics.dict()
    total_pop = demo_dict.get("total_population", 1) # Avoid division by zero

    for segment in category.target_segments:
        weight = segment.weight
        max_possible += weight
        
        # Get actual population for this segment
        segment_pop = demo_dict.get(segment.segment, 0)
        
        # Normalize it somewhat (ratio of total pop). E.g., if target is working pop (50% of total)
        # We give a score relative to its size. 
        # This is a simplified deterministic matching function.
        ratio = segment_pop / total_pop if total_pop > 0 else 0
        
        # Suppose a good ratio is > 10%
        segment_score = min(ratio * 10.0, 1.0) * 100 * weight
        total_score += segment_score
        signals[segment.segment] = {"population": segment_pop, "ratio": round(ratio, 2)}

    # Normalize to 0-100
    final_score = (total_score / max_possible) if max_possible > 0 else 50.0
    final_score = clamp_score(final_score)

    return {
        "demographic_fit": round(final_score, 2),
        "confidence": ConfidenceLevel.HIGH if demographics else ConfidenceLevel.LOW,
        "signals": signals
    }
