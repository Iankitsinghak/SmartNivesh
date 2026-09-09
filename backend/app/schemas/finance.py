from pydantic import BaseModel, Field
from typing import Optional
from app.core.enums import DataStatus

class ValueWithStatus(BaseModel):
    value: Optional[float] = None
    status: DataStatus
    notes: Optional[str] = None
    methodology: Optional[str] = None

class RevenueAssumptions(BaseModel):
    units_per_month: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, ge=0)
    operating_days_per_month: Optional[int] = Field(None, ge=1, le=31)

class CostAssumptions(BaseModel):
    variable_cost_ratio: Optional[float] = Field(None, ge=0, le=1)
    fixed_costs_per_month: Optional[float] = Field(None, ge=0)
    initial_inventory: Optional[float] = Field(None, ge=0)
    operating_buffer_months: Optional[float] = Field(None, ge=0)

class LoanAssumptions(BaseModel):
    annual_interest_rate: float = Field(..., ge=0)
    tenure_months: int = Field(..., gt=0)

class FinancialAnalysisRequest(BaseModel):
    available_margin: float = Field(..., ge=0)
    revenue_assumptions: RevenueAssumptions = RevenueAssumptions()
    cost_assumptions: CostAssumptions = CostAssumptions()
    loan_assumptions: LoanAssumptions

class ScenarioResult(BaseModel):
    scenario_type: str
    revenue: ValueWithStatus
    variable_cost: ValueWithStatus
    fixed_cost: ValueWithStatus
    operating_profit: ValueWithStatus
    repayment_coverage: ValueWithStatus

class RecommendedFinancing(BaseModel):
    requested_project_cost: float
    recommended_project_cost: float
    required_margin: float
    recommended_loan: float
    monthly_emi: float
    base_repayment_coverage: Optional[float] = None
    conservative_repayment_coverage: Optional[float] = None
    financial_feasibility: str

class FinancialFeasibilityIndicators(BaseModel):
    financial_score: ValueWithStatus
    break_even_units: ValueWithStatus
    working_capital_requirement: ValueWithStatus

class FinancialAnalysisResponse(BaseModel):
    project_cost: ValueWithStatus
    margin_contribution: ValueWithStatus
    loan_amount: ValueWithStatus
    monthly_emi: ValueWithStatus
    total_repayment: ValueWithStatus
    total_interest: ValueWithStatus
    
    base_scenario: ScenarioResult
    conservative_scenario: ScenarioResult
    optimistic_scenario: ScenarioResult
    
    recommended_financing: RecommendedFinancing
    feasibility_indicators: FinancialFeasibilityIndicators
