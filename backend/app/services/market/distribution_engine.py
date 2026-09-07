from app.schemas.business import BusinessCategory
from app.schemas.market import DistributionResult
from app.utils.provenance import ConfidenceLevel

def analyze_distribution(category: BusinessCategory) -> DistributionResult:
    """
    In the absence of a reliable wholesale market dataset, this returns a default
    or estimated distribution profile based on business category requirements.
    Never invents exact travel times or hub locations without data.
    """
    requires_wholesale = category.distribution_profile.get("requires_wholesale", False)
    
    # Dummy fallback
    if requires_wholesale:
        score = 50.0 
        level = "MODERATE"
    else:
        score = 80.0
        level = "HIGH"
        
    return DistributionResult(
        distribution_score=score,
        distribution_level=level,
        nearest_relevant_hubs=[],
        supplier_signals=["Distribution data unavailable. Using default estimates."],
        confidence=ConfidenceLevel.LOW
    )
