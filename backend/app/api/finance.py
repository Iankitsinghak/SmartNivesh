from fastapi import APIRouter, HTTPException
from app.schemas.finance import FinancialAnalysisRequest, FinancialAnalysisResponse
from app.services.finance.finance_engine import analyze_finance

router = APIRouter(prefix="/api/finance", tags=["Financial Intelligence"])

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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))

