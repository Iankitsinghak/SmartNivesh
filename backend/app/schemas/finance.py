from decimal import Decimal
from pydantic import BaseModel, Field, model_validator
from typing import Dict, Literal, Optional, List
from app.core.enums import FinancialStatus, FinancingBand, DataClassification
from app.schemas.common import DataProvenance

FinancialDataStatus = Literal["CALCULATED", "ESTIMATED", "ASSUMPTION", "UNKNOWN"]


class RevenueAssumptions(BaseModel):
    monthly_revenue: Optional[Decimal] = Field(default=None, ge=0, le=Decimal("100000000000"))
    units_sold: Optional[Decimal] = Field(default=None, ge=0, le=Decimal("1000000000"))
    daily_units: Optional[Decimal] = Field(default=None, ge=0, le=Decimal("1000000000"))
    operating_days: Optional[Decimal] = Field(default=None, ge=0, le=Decimal("366"))
    selling_price: Optional[Decimal] = Field(default=None, ge=0, le=Decimal("1000000000"))

    @model_validator(mode="after")
    def validate_unit_model(self):
        if self.monthly_revenue is not None and any(value is not None for value in (self.units_sold, self.daily_units, self.operating_days, self.selling_price)):
            raise ValueError("Provide direct monthly_revenue or a unit-based revenue model, not both.")
        if self.units_sold is not None and self.daily_units is not None:
            raise ValueError("Provide either units_sold or daily_units, not both.")
        if self.daily_units is not None and self.operating_days is None:
            raise ValueError("operating_days is required when daily_units is provided.")
        if self.operating_days is not None and self.daily_units is None:
            raise ValueError("daily_units is required when operating_days is provided.")
        return self


class CostAssumptions(BaseModel):
    monthly_variable_cost: Optional[Decimal] = Field(default=None, ge=0)
    monthly_fixed_cost: Optional[Decimal] = Field(default=None, ge=0)
    variable_cost_ratio: Optional[Decimal] = Field(default=None, ge=0, le=1)
    variable_cost_per_unit: Optional[Decimal] = Field(default=None, ge=0, le=Decimal("1000000000"))
    rent: Optional[Decimal] = Field(default=None, ge=0)
    salaries: Optional[Decimal] = Field(default=None, ge=0)
    utilities: Optional[Decimal] = Field(default=None, ge=0)
    maintenance: Optional[Decimal] = Field(default=None, ge=0)
    insurance: Optional[Decimal] = Field(default=None, ge=0)
    other_fixed_costs: Optional[Decimal] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_variable_cost_model(self):
        methods = [self.monthly_variable_cost, self.variable_cost_ratio, self.variable_cost_per_unit]
        if sum(value is not None for value in methods) > 1:
            raise ValueError("Provide only one variable-cost method.")
        return self


class WorkingCapitalAssumptions(BaseModel):
    initial_inventory: Optional[Decimal] = Field(default=None, ge=0)
    operating_cash_requirement: Optional[Decimal] = Field(default=None, ge=0)
    receivables: Optional[Decimal] = Field(default=None, ge=0)
    supplier_credit: Optional[Decimal] = Field(default=None, ge=0)
    operating_buffer_months: Optional[Decimal] = Field(default=None, ge=0, le=24)


class LoanAssumptions(BaseModel):
    annual_interest_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    tenure_months: Optional[int] = Field(default=None, gt=0, le=600)

    @model_validator(mode="after")
    def validate_complete_loan_terms(self):
        if (self.annual_interest_rate is None) != (self.tenure_months is None):
            raise ValueError("annual_interest_rate and tenure_months must be supplied together.")
        return self


class ScenarioConfiguration(BaseModel):
    conservative_revenue_multiplier: Decimal = Field(default=Decimal("0.80"), ge=0, le=2)
    conservative_cost_multiplier: Decimal = Field(default=Decimal("1.10"), ge=0, le=3)
    optimistic_revenue_multiplier: Decimal = Field(default=Decimal("1.15"), ge=0, le=3)
    optimistic_cost_multiplier: Decimal = Field(default=Decimal("0.95"), ge=0, le=3)


class FinancialAnalysisRequest(BaseModel):
    available_margin_capital: Decimal = Field(..., gt=0, le=Decimal("100000000"), description="The margin money available with the entrepreneur.")
    margin_percentage: Decimal = Field(default=Decimal("0.10"), gt=0, le=1)
    revenue: Optional[RevenueAssumptions] = None
    costs: Optional[CostAssumptions] = None
    working_capital: Optional[WorkingCapitalAssumptions] = None
    loan: Optional[LoanAssumptions] = None
    scenarios: ScenarioConfiguration = Field(default_factory=ScenarioConfiguration)


class RevenueResult(BaseModel):
    status: FinancialDataStatus
    monthly_revenue: Optional[float] = None
    monthly_units: Optional[float] = None
    methodology: str


class CostResult(BaseModel):
    status: FinancialDataStatus
    variable_cost: Optional[float] = None
    fixed_cost: Optional[float] = None
    total_operating_cost: Optional[float] = None
    operating_profit: Optional[float] = None
    methodology: List[str] = []


class WorkingCapitalResult(BaseModel):
    status: FinancialDataStatus
    requirement: Optional[float] = None
    methodology: str


class RepaymentMetrics(BaseModel):
    status: FinancialDataStatus
    available_monthly_cash: Optional[float] = None
    repayment_coverage: Optional[float] = None
    monthly_cash_surplus: Optional[float] = None
    methodology: str


class BreakEvenResult(BaseModel):
    status: FinancialDataStatus
    contribution_per_unit: Optional[float] = None
    break_even_units: Optional[float] = None
    methodology: str


class ScenarioResult(BaseModel):
    name: Literal["CONSERVATIVE", "BASE", "OPTIMISTIC"]
    status: FinancialDataStatus
    revenue_multiplier: float
    cost_multiplier: float
    monthly_revenue: Optional[float] = None
    monthly_operating_cost: Optional[float] = None
    operating_profit: Optional[float] = None
    repayment_coverage: Optional[float] = None
    monthly_cash_after_emi: Optional[float] = None


class FinancingRecommendation(BaseModel):
    status: FinancialDataStatus
    requested_project_cost: float
    recommended_project_cost: Optional[float] = None
    required_margin: Optional[float] = None
    recommended_loan: Optional[float] = None
    monthly_emi: Optional[float] = None
    base_repayment_coverage: Optional[float] = None
    conservative_repayment_coverage: Optional[float] = None
    financial_feasibility: Literal["COMFORTABLE", "TIGHT", "UNAFFORDABLE", "UNKNOWN"]
    methodology: List[str] = []


class FinancialFeasibility(BaseModel):
    status: Literal["COMFORTABLE", "TIGHT", "UNAFFORDABLE", "UNKNOWN"]
    repayment_coverage: Optional[float] = None
    conservative_repayment_coverage: Optional[float] = None
    monthly_cash_surplus: Optional[float] = None
    downside_status: Literal["POSITIVE", "NEGATIVE", "UNKNOWN"]
    methodology: str

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
    revenue: Optional[RevenueResult] = None
    costs: Optional[CostResult] = None
    working_capital: Optional[WorkingCapitalResult] = None
    repayment_metrics: Optional[RepaymentMetrics] = None
    break_even: Optional[BreakEvenResult] = None
    scenario_results: List[ScenarioResult] = []
    recommendation: Optional[FinancingRecommendation] = None
    feasibility: Optional[FinancialFeasibility] = None
    assumptions: List[str] = []
    limitations: List[str] = []


class FinancialRoadmapRequest(BaseModel):
    """Inputs explicitly needed to calculate the curated scheme roadmap."""

    margin_capital: float = Field(gt=0, le=100_000_000)
    activity_type: Literal["service_or_trading", "manufacturing", "food_processing", "traditional_artisan", "not_sure"] = "not_sure"
    area_type: Literal["rural", "urban", "not_sure"] = "not_sure"
    pmegp_beneficiary_group: Literal["general", "special", "not_sure"] = "not_sure"
    has_repaid_mudra_tarun: bool = False
    vishwakarma_loan_stage: Literal["not_confirmed", "first", "second"] = "not_confirmed"
    monthly_fixed_cost: Optional[float] = Field(default=None, ge=0)
    monthly_variable_cost: Optional[float] = Field(default=None, ge=0)
    expected_monthly_revenue: Optional[float] = Field(default=None, ge=0)
    operating_reserve_months: Optional[float] = Field(default=None, ge=0, le=24)


class FinancialAssessment(BaseModel):
    status: Literal["VALID", "OUTSIDE_BASELINE_RANGE"]
    margin_capital: float
    project_cost: float
    requested_loan: float
    message: Optional[str] = None
    eligible_loan: Optional[float] = None
    required_own_contribution: Optional[float] = None
    scheme_name: Optional[str] = None
    annual_interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    moratorium_months: Optional[int] = None
    repayment_months: Optional[int] = None
    repayment_quarters: Optional[int] = None
    estimated_monthly_instalment: Optional[float] = None
    estimated_quarterly_instalment: Optional[float] = None
    estimated_total_repayment: Optional[float] = None
    estimated_total_interest: Optional[float] = None
    repayment_frequency_note: str
    calculation_limitations: List[str] = []


class CashflowAssessment(BaseModel):
    status: Literal["INCOMPLETE", "AVAILABLE"]
    monthly_operating_cost: Optional[float] = None
    monthly_cash_before_debt: Optional[float] = None
    monthly_cash_after_baseline_instalment: Optional[float] = None
    operating_reserve_requirement: Optional[float] = None
    limitations: List[str] = []


class GovernmentSchemeRoute(BaseModel):
    code: str
    name: str
    administering_body: str
    status: Literal["PUBLISHED_TERMS", "PROFILE_NEEDED", "ELIGIBILITY_CHECK", "LENDER_TERMS_REQUIRED", "AVAILABILITY_CHECK", "NOT_APPLICABLE"]
    summary: str
    official_url: str
    source_verified_on: str
    funding_limit: Optional[float] = None
    beneficiary_interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    moratorium_months: Optional[int] = None
    estimated_monthly_instalment: Optional[float] = None
    estimated_quarterly_instalment: Optional[float] = None
    potential_subsidy: Optional[float] = None
    minimum_beneficiary_contribution: Optional[float] = None
    conditions: List[str] = []
    limitations: List[str] = []


class FinancialRoadmapResponse(BaseModel):
    assessment: FinancialAssessment
    cashflow: CashflowAssessment
    routes: List[GovernmentSchemeRoute]
    readiness_actions: List[str]
    data_status: Literal["VERIFIED_GOVERNMENT_RULES"]
    data_limitations: List[str]
