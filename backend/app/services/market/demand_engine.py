from app.schemas.market import DemandResult, BusinessActivityResult, POIResult
from app.core.enums import ConfidenceLevel
from app.utils.normalization import get_generic_level, clamp_score

def analyze_demand(
    demographic_fit_score: float,
    poi_result: POIResult,
    activity_result: BusinessActivityResult
) -> DemandResult:
    """
    Combines Demographics, POIs, and Business Activity into a unified Demand score.
    """
    # Simple deterministic combination
    # 40% Demographics, 30% POIs, 30% Activity
    poi_score = min(len(poi_result.relevant_signals) * 15.0, 100.0) # Up to ~7 relevant POIs for 100%
    
    demand_score = (
        (demographic_fit_score * 0.40) +
        (poi_score * 0.30) +
        (activity_result.commercial_activity_score * 0.30)
    )
    
    demand_score = clamp_score(demand_score)
    
    return DemandResult(
        demand_score=round(demand_score, 2),
        demand_level=get_generic_level(demand_score),
        signals={
            "demographic_fit": round(demographic_fit_score, 2),
            "poi_relevance": round(poi_score, 2),
            "business_activity": round(activity_result.commercial_activity_score, 2)
        },
        confidence=ConfidenceLevel.MEDIUM
    )
