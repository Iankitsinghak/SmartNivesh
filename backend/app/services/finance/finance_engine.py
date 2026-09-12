import logging
from decimal import Decimal, ROUND_HALF_UP

from app.core.enums import ConfidenceLevel, DataClassification, FinancialStatus, FinancingBand
from app.schemas.common import DataProvenance
from app.schemas.finance import (
    BreakEvenResult,
    CostResult,
    FinancialAnalysisRequest,
    FinancialAnalysisResponse,
    FinancialFeasibility,
    RepaymentMetrics,
    RevenueResult,
    WorkingCapitalResult,
)
from app.services.finance.emi import calculate_deterministic_emi
from app.services.finance.loan_engine import (
    calculate_break_even,
    calculate_costs,
    calculate_revenue,
    calculate_working_capital,
    decimal_value,
    derive_financing_structure,
    determine_financing_band,
    money,
)
from app.services.finance.recommended_financing import calculate_recommended_financing
from app.services.finance.repayment import generate_amortization_schedule
from app.services.finance.scenarios import generate_all_scenarios


logger = logging.getLogger(__name__)


def _float(value: Decimal | None) -> float | None:
    return None if value is None else float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _unknown_extensions(reason: str) -> dict:
    return {
        "revenue": RevenueResult(status="UNKNOWN", methodology="Revenue assumptions were not evaluated."),
        "costs": CostResult(status="UNKNOWN", methodology=["Operating costs were not evaluated."]),
        "working_capital": WorkingCapitalResult(status="UNKNOWN", methodology="Working capital was not evaluated."),
        "repayment_metrics": RepaymentMetrics(status="UNKNOWN", methodology="Repayment Coverage is unavailable."),
        "break_even": BreakEvenResult(status="UNKNOWN", methodology="Break-even is unavailable."),
        "scenario_results": [],
        "recommendation": None,
        "feasibility": FinancialFeasibility(status="UNKNOWN", downside_status="UNKNOWN", methodology=reason),
        "limitations": [reason],
    }


def analyze_finance(request: FinancialAnalysisRequest) -> FinancialAnalysisResponse:
    """Orchestrate deterministic financial analysis without inventing business inputs."""
    logger.info("Financial analysis started")
    margin = decimal_value(request.available_margin_capital)
    project_cost, margin_contribution, loan_requirement = derive_financing_structure(
        margin, request.margin_percentage
    )
    band, params = determine_financing_band(float(project_cost))

    if band == FinancingBand.UNSUPPORTED and not request.loan:
        reason = "Project cost is outside the configured baseline financing range; supply explicit loan terms to model repayment."
        logger.info("Financial analysis completed with unsupported baseline range")
        return FinancialAnalysisResponse(
            available_margin_capital=_float(margin_contribution), calculated_project_cost=_float(project_cost),
            calculated_loan_requirement=_float(loan_requirement), applicable_financing_band=band,
            actual_modeled_loan=0.0, financing_gap=_float(loan_requirement), monthly_emi=0.0,
            total_repayment=0.0, total_interest=0.0, repayment_schedule=[],
            financial_status=FinancialStatus.PROJECT_RANGE_EXCEEDED,
            **_unknown_extensions(reason),
        )

    user_loan_terms = bool(request.loan and request.loan.annual_interest_rate is not None)
    if user_loan_terms:
        interest_rate = decimal_value(request.loan.annual_interest_rate)
        tenure_months = int(request.loan.tenure_months)
        moratorium_months = 0
        max_agency_loan = None
        actual_modeled_loan = loan_requirement
        financing_gap = Decimal(0)
        status = FinancialStatus.SUPPORTED
        loan_term_note = "Interest rate and tenure are user-supplied assumptions; no scheme eligibility is inferred."
    else:
        interest_rate = decimal_value(params.get("interest_rate", 0))
        tenure_months = int(params.get("tenure_months", 0))
        moratorium_months = int(params.get("moratorium_months", 0))
        max_agency_loan = decimal_value(params.get("maximum_agency_loan", 0))
        actual_modeled_loan = min(loan_requirement, max_agency_loan)
        financing_gap = money(loan_requirement - actual_modeled_loan)
        status = FinancialStatus.LOAN_CAP_EXCEEDED if financing_gap > 0 else FinancialStatus.SUPPORTED
        loan_term_note = "Repayment uses the configured published baseline; final eligibility and lender terms are external."

    monthly_emi = Decimal(str(calculate_deterministic_emi(actual_modeled_loan, interest_rate, tenure_months)))
    schedule = generate_amortization_schedule(
        float(actual_modeled_loan), float(interest_rate), tenure_months, float(monthly_emi)
    )
    total_repayment = money(sum((Decimal(str(row.payment)) for row in schedule), Decimal(0)))
    total_interest = money(sum((Decimal(str(row.interest_component)) for row in schedule), Decimal(0)))

    monthly_revenue, monthly_units, revenue_method = calculate_revenue(request.revenue)
    variable_cost, fixed_cost, operating_cost, operating_profit, cost_methods = calculate_costs(
        monthly_revenue, monthly_units, request.costs
    )
    working_capital, working_capital_method = calculate_working_capital(request.working_capital, operating_cost)
    contribution, break_even_units, break_even_method = calculate_break_even(request.revenue, request.costs, fixed_cost)
    scenarios = generate_all_scenarios(monthly_revenue, operating_cost, monthly_emi, request.scenarios)
    conservative = next((item for item in scenarios if item.name == "CONSERVATIVE"), None)

    coverage = operating_profit / monthly_emi if operating_profit is not None and monthly_emi > 0 else None
    cash_surplus = operating_profit - monthly_emi if operating_profit is not None else None
    conservative_coverage = (
        Decimal(str(conservative.repayment_coverage))
        if conservative and conservative.repayment_coverage is not None else None
    )
    if coverage is None or conservative_coverage is None:
        feasibility_status, downside_status = "UNKNOWN", "UNKNOWN"
    elif conservative_coverage >= Decimal("1.50"):
        feasibility_status, downside_status = "COMFORTABLE", "POSITIVE"
    elif conservative_coverage >= Decimal("1.20"):
        feasibility_status, downside_status = "TIGHT", "POSITIVE"
    else:
        feasibility_status, downside_status = "UNAFFORDABLE", "NEGATIVE"

    recommendation = calculate_recommended_financing(
        project_cost, margin_contribution, loan_requirement, interest_rate, tenure_months, scenarios
    )
    assumptions = [
        "Available margin and margin percentage are user-supplied assumptions.", loan_term_note,
        "Scenario multipliers are explicit: conservative revenue "
        f"{request.scenarios.conservative_revenue_multiplier}× / cost {request.scenarios.conservative_cost_multiplier}×; "
        f"optimistic revenue {request.scenarios.optimistic_revenue_multiplier}× / cost {request.scenarios.optimistic_cost_multiplier}×.",
    ]
    limitations = []
    if monthly_revenue is None:
        limitations.append("Revenue is UNKNOWN until selling price and sales volume are supplied.")
    if operating_cost is None:
        limitations.append("Operating profit is UNKNOWN until compatible cost inputs are supplied.")
    if working_capital is None:
        limitations.append(working_capital_method)

    logger.info("Financial analysis completed")
    return FinancialAnalysisResponse(
        available_margin_capital=_float(margin_contribution), calculated_project_cost=_float(project_cost),
        calculated_loan_requirement=_float(loan_requirement), applicable_financing_band=band,
        interest_rate=float(interest_rate), tenure_months=tenure_months, moratorium_months=moratorium_months,
        maximum_agency_loan=_float(max_agency_loan), actual_modeled_loan=_float(actual_modeled_loan),
        financing_gap=_float(financing_gap), monthly_emi=_float(monthly_emi),
        total_repayment=_float(total_repayment), total_interest=_float(total_interest), repayment_schedule=schedule,
        financial_status=status, data_classification=DataClassification.CALCULATED,
        provenance=[DataProvenance(
            source_id="financial_intelligence_engine", source_name="GramVyapar deterministic financial methodology",
            data_type=DataClassification.CALCULATED, confidence=ConfidenceLevel.HIGH, notes=loan_term_note,
        )],
        revenue=RevenueResult(
            status="CALCULATED" if monthly_revenue is not None else "UNKNOWN",
            monthly_revenue=_float(monthly_revenue), monthly_units=_float(monthly_units), methodology=revenue_method,
        ),
        costs=CostResult(
            status="CALCULATED" if operating_cost is not None else "UNKNOWN",
            variable_cost=_float(variable_cost), fixed_cost=_float(fixed_cost),
            total_operating_cost=_float(operating_cost), operating_profit=_float(operating_profit), methodology=cost_methods,
        ),
        working_capital=WorkingCapitalResult(
            status="ESTIMATED" if working_capital is not None else "UNKNOWN",
            requirement=_float(working_capital), methodology=working_capital_method,
        ),
        repayment_metrics=RepaymentMetrics(
            status="CALCULATED" if coverage is not None else "UNKNOWN", available_monthly_cash=_float(operating_profit),
            repayment_coverage=None if coverage is None else float(coverage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            monthly_cash_surplus=_float(cash_surplus),
            methodology="Repayment Coverage = monthly operating profit ÷ EMI; this is not formal DSCR.",
        ),
        break_even=BreakEvenResult(
            status="CALCULATED" if break_even_units is not None else "UNKNOWN",
            contribution_per_unit=_float(contribution), break_even_units=_float(break_even_units), methodology=break_even_method,
        ),
        scenario_results=scenarios, recommendation=recommendation,
        feasibility=FinancialFeasibility(
            status=feasibility_status,
            repayment_coverage=None if coverage is None else float(coverage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            conservative_repayment_coverage=None if conservative_coverage is None else float(conservative_coverage),
            monthly_cash_surplus=_float(cash_surplus), downside_status=downside_status,
            methodology="Feasibility uses explicit base and conservative Repayment Coverage; no demand is inferred.",
        ),
        assumptions=assumptions, limitations=limitations,
    )
