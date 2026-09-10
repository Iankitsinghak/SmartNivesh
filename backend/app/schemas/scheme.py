from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.enums import FinancingBand, EligibilityStatus

class SchemeRoutingRequest(BaseModel):
    project_cost: float = Field(..., description="Project cost derived by the Financial Engine")
    loan_requirement: float = Field(..., description="Loan requirement derived by the Financial Engine")
    financing_band: FinancingBand = Field(..., description="The financing band identified by the Financial Engine")
    actual_modeled_loan: float = Field(..., description="The actual loan modeled by the Financial Engine after applying caps")
    financing_gap: float = Field(..., description="Any financing gap calculated by the Financial Engine")

class SchemeRoutingResponse(BaseModel):
    scheme_code: Optional[str] = None
    scheme_name: Optional[str] = None
    applicable: bool
    project_cost: float
    loan_requirement: float
    maximum_loan: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_years: Optional[int] = None
    moratorium_months: Optional[int] = None
    financing_percentage: Optional[float] = None
    loan_cap_exceeded: bool
    financing_gap: float
    eligibility_status: EligibilityStatus
    missing_eligibility_inputs: List[str] = []
    rule_status: str
