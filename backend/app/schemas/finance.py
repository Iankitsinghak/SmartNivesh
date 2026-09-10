from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.enums import FinancialStatus, FinancingBand, DataClassification
from app.schemas.common import DataProvenance

class FinancialAnalysisRequest(BaseModel):
    available_margin_capital: float = Field(..., gt=0, description="The margin money available with the entrepreneur.")

class RepaymentScheduleRow(BaseModel):
    installment_number: int
    opening_balance: float
    interest_component: float
    principal_component: float
    payment: float
    closing_balance: float

class FinancialAnalysisResponse(BaseModel):
    available_margin_capital: float
    calculated_project_cost: float
    calculated_loan_requirement: float
    applicable_financing_band: FinancingBand
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    moratorium_months: Optional[int] = None
    maximum_agency_loan: Optional[float] = None
    actual_modeled_loan: float
    financing_gap: float
    monthly_emi: float
    total_repayment: float
    total_interest: float
    repayment_schedule: List[RepaymentScheduleRow] = []
    financial_status: FinancialStatus
    data_classification: DataClassification = DataClassification.CALCULATED
    provenance: List[DataProvenance] = []

