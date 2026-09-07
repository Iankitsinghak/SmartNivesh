from app.schemas.market import PurchasingPowerResult
from app.utils.provenance import ConfidenceLevel

def analyze_purchasing_power(lat: float, lon: float) -> PurchasingPowerResult:
    """
    Since there is no reliable dataset for exact village-level income,
    we return an UNKNOWN/ESTIMATED proxy and LOW confidence.
    We NEVER fabricate income numbers.
    """
    return PurchasingPowerResult(
        purchasing_power_score=50.0,
        purchasing_power_level="UNKNOWN",
        confidence=ConfidenceLevel.LOW
    )
