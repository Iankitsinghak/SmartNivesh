from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.schemas.finance import FinancingRecommendation, ScenarioResult
from app.services.finance.emi import calculate_deterministic_emi


def _rounded(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_recommended_financing(
    requested_project_cost: Decimal,
    margin: Decimal,
    requested_loan: Decimal,
    annual_interest_rate: Decimal,
    tenure_months: int,
    scenarios: list[ScenarioResult],
    minimum_conservative_coverage: Decimal = Decimal("1.20"),
) -> FinancingRecommendation:
    """Choose the largest tested loan whose conservative cash covers repayment.

    This is a financial-comfort recommendation, never a scheme eligibility result.
    """
    base = next((item for item in scenarios if item.name == "BASE"), None)
    conservative = next((item for item in scenarios if item.name == "CONSERVATIVE"), None)
    if not base or not conservative or base.operating_profit is None or conservative.operating_profit is None:
        return FinancingRecommendation(
            status="UNKNOWN", requested_project_cost=_rounded(requested_project_cost),
            financial_feasibility="UNKNOWN",
            methodology=["Revenue and operating-cost assumptions are required before financing can be recommended."],
        )

    base_cash = Decimal(str(base.operating_profit))
    conservative_cash = Decimal(str(conservative.operating_profit))
    selected: Optional[tuple[Decimal, Decimal, Decimal, Decimal]] = None
    for fraction in (Decimal("1.00"), Decimal("0.90"), Decimal("0.75"), Decimal("0.50"), Decimal("0.25")):
        candidate_loan = (requested_loan * fraction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        candidate_emi = Decimal(str(calculate_deterministic_emi(candidate_loan, annual_interest_rate, tenure_months)))
        if candidate_emi == 0:
            continue
        base_coverage = base_cash / candidate_emi
        conservative_coverage = conservative_cash / candidate_emi
        if conservative_coverage >= minimum_conservative_coverage:
            selected = candidate_loan, candidate_emi, base_coverage, conservative_coverage
            break

    if selected is None:
        return FinancingRecommendation(
            status="CALCULATED", requested_project_cost=_rounded(requested_project_cost),
            financial_feasibility="UNAFFORDABLE",
            base_repayment_coverage=None,
            conservative_repayment_coverage=None,
            methodology=[
                "No tested loan from 25% to 100% of the requested amount achieved 1.20× conservative Repayment Coverage.",
                "A lower project cost, higher verified margin, or stronger evidenced cash flow is required.",
            ],
        )

    loan, emi, base_coverage, conservative_coverage = selected
    project_cost = margin + loan
    feasibility = "COMFORTABLE" if conservative_coverage >= Decimal("1.50") else "TIGHT"
    return FinancingRecommendation(
        status="CALCULATED",
        requested_project_cost=_rounded(requested_project_cost),
        recommended_project_cost=_rounded(project_cost),
        required_margin=_rounded(margin),
        recommended_loan=_rounded(loan),
        monthly_emi=_rounded(emi),
        base_repayment_coverage=float(base_coverage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        conservative_repayment_coverage=float(conservative_coverage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        financial_feasibility=feasibility,
        methodology=[
            "Candidate loans are tested at 100%, 90%, 75%, 50% and 25% of the requested financing.",
            "The largest candidate with at least 1.20× conservative Repayment Coverage is recommended.",
            "This is financial comfort analysis, not maximum eligibility or a sanction.",
        ],
    )
