import logging

from fastapi import APIRouter, HTTPException
from app.schemas.finance import FinancialAnalysisRequest, FinancialAnalysisResponse, FinancialRoadmapRequest, FinancialRoadmapResponse
from app.services.finance.finance_engine import analyze_finance
from app.services.finance.scheme_router import build_financial_roadmap

router = APIRouter(prefix="/api/finance", tags=["Financial Intelligence"])
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=FinancialAnalysisResponse)
async def analyze_finance_endpoint(request: FinancialAnalysisRequest):
    """
    Analyzes the financial feasibility of a proposed business.
    Calculates project cost, loan requirement, EMI, and repayment schedule
    based on the available margin capital.
    """
    try:
        response = analyze_finance(request)
        return response
    except ValueError as exc:
        logger.info("Financial analysis validation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Financial analysis failed")
        raise HTTPException(
            status_code=500,
            detail="Financial analysis could not be completed. Please try again.",
        )


@router.post("/roadmap", response_model=FinancialRoadmapResponse)
async def financial_roadmap_endpoint(request: FinancialRoadmapRequest):
    """Return evidence-labelled finance calculations and official scheme routes."""
    try:
        return build_financial_roadmap(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
