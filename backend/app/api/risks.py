"""
Risk analysis API endpoint.

Orchestration-only: accepts location, category, optional operational evidence,
and delegates to the risk service. Returns structured threat analysis with
evidence, confidence, limitations, and recommendations.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.common import Location
from app.schemas.risk import RiskAnalysisRequest, RiskAnalysisResponse
from app.services.location.resolver import get_location
from app.services.risk.risk_engine import analyze_risk

router = APIRouter(prefix="/api/risks", tags=["Risk Analysis"])


@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_risks_endpoint(request: RiskAnalysisRequest) -> RiskAnalysisResponse:
    """
    Analyze threats at a location for a business category.
    
    Threats include seasonal demand fluctuations, supply-chain bottlenecks,
    and buyer concentration. Each threat is evidence-gated: missing or
    insufficient verified data results in UNKNOWN status, not a fabricated score.
    
    Accepts optional operational evidence (supplier data, buyer metrics, seasonal
    observations) for higher-confidence analysis. All evidence must be validated
    and dated; stale or invalid evidence is rejected.
    
    Returns structured threat items with severity, confidence, limitations,
    methodology, and deterministic mitigation recommendations.
    """
    try:
        # Resolve location
        location = get_location(request.location_id)
        if not location:
            raise HTTPException(status_code=400, detail="Location not found")
        
        # Analyze risk
        response = analyze_risk(
            location=location,
            category_id=request.category_id,
            radius_km=request.radius_km,
            operational_evidence=request.operational_evidence,
        )
        
        return response
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
