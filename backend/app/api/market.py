from fastapi import APIRouter, HTTPException
from app.schemas.market import MarketAnalysisRequest, MarketAnalysisResponse
from app.services.market.market_engine import analyze_market

router = APIRouter(prefix="/api/market", tags=["Market Intelligence"])

@router.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market_endpoint(request: MarketAnalysisRequest):
    """
    Analyzes the local area market for a selected business category at a given location.
    Provides highly structured, evidence-backed deterministic metrics without AI generation.
    """
    try:
        response = analyze_market(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))
