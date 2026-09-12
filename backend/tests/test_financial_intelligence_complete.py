from pydantic import ValidationError
import pytest

from app.schemas.finance import FinancialAnalysisRequest
from app.services.finance.emi import calculate_deterministic_emi
from app.services.finance.finance_engine import analyze_finance


def complete_request(**overrides):
    payload = {
        "available_margin_capital": 100_000,
        "revenue": {"daily_units": 30, "operating_days": 26, "selling_price": 500},
        "costs": {
            "variable_cost_per_unit": 200, "rent": 20_000, "salaries": 40_000,
            "utilities": 5_000, "maintenance": 3_000, "insurance": 1_000,
            "other_fixed_costs": 1_000,
        },
        "working_capital": {
            "initial_inventory": 50_000, "operating_cash_requirement": 20_000,
            "receivables": 10_000, "supplier_credit": 5_000, "operating_buffer_months": 2,
        },
    }
    payload.update(overrides)
    return FinancialAnalysisRequest(**payload)


def test_complete_revenue_cost_profit_working_capital_and_break_even():
    result = analyze_finance(complete_request())
    assert result.calculated_project_cost == 1_000_000
    assert result.calculated_loan_requirement == 900_000
    assert result.revenue.monthly_revenue == 390_000
    assert result.costs.variable_cost == 156_000
    assert result.costs.fixed_cost == 70_000
    assert result.costs.total_operating_cost == 226_000
    assert result.costs.operating_profit == 164_000
    assert result.working_capital.requirement == 527_000
    assert result.break_even.contribution_per_unit == 300
    assert result.break_even.break_even_units == pytest.approx(233.33)


def test_repayment_coverage_and_scenarios_are_deterministic():
    request = complete_request()
    first = analyze_finance(request)
    second = analyze_finance(request)
    assert first.model_dump() == second.model_dump()
    assert first.repayment_metrics.status == "CALCULATED"
    assert first.repayment_metrics.repayment_coverage > 1
    assert [item.name for item in first.scenario_results] == ["CONSERVATIVE", "BASE", "OPTIMISTIC"]
    assert all(item.status == "CALCULATED" for item in first.scenario_results)


def test_recommendation_reduces_uncomfortable_requested_financing():
    result = analyze_finance(FinancialAnalysisRequest(
        available_margin_capital=100_000,
        revenue={"units_sold": 1_500, "selling_price": 100},
        costs={"variable_cost_ratio": 0.5, "rent": 25_000},
    ))
    assert result.recommendation.status == "CALCULATED"
    assert result.recommendation.recommended_loan < result.calculated_loan_requirement
    assert result.recommendation.conservative_repayment_coverage >= 1.2


def test_missing_business_inputs_remain_unknown():
    result = analyze_finance(FinancialAnalysisRequest(available_margin_capital=100_000))
    assert result.revenue.status == "UNKNOWN"
    assert result.costs.status == "UNKNOWN"
    assert result.working_capital.status == "UNKNOWN"
    assert result.repayment_metrics.status == "UNKNOWN"
    assert result.break_even.status == "UNKNOWN"
    assert result.feasibility.status == "UNKNOWN"
    assert result.recommendation.status == "UNKNOWN"


def test_impossible_break_even_is_explained():
    result = analyze_finance(FinancialAnalysisRequest(
        available_margin_capital=10_000,
        revenue={"units_sold": 100, "selling_price": 50},
        costs={"variable_cost_per_unit": 60, "rent": 1_000},
    ))
    assert result.break_even.status == "UNKNOWN"
    assert result.break_even.contribution_per_unit == -10
    assert "impossible" in result.break_even.methodology.lower()


@pytest.mark.parametrize("payload", [
    {"available_margin_capital": -1},
    {"available_margin_capital": 10_000, "costs": {"variable_cost_ratio": 1.01}},
    {"available_margin_capital": 10_000, "loan": {"annual_interest_rate": 8}},
    {"available_margin_capital": 10_000, "revenue": {"daily_units": 10, "selling_price": 20}},
    {"available_margin_capital": 10_000, "revenue": {"units_sold": 10, "daily_units": 2, "operating_days": 5, "selling_price": 20}},
])
def test_invalid_financial_inputs_are_rejected(payload):
    with pytest.raises(ValidationError):
        FinancialAnalysisRequest(**payload)


def test_emi_validation_and_zero_interest_precision():
    assert calculate_deterministic_emi(100_000, 0, 10) == 10_000
    with pytest.raises(ValueError):
        calculate_deterministic_emi(-1, 8, 12)
    with pytest.raises(ValueError):
        calculate_deterministic_emi(100_000, -1, 12)
    with pytest.raises(ValueError):
        calculate_deterministic_emi(100_000, 8, 0)


def test_explicit_loan_terms_support_large_projects_without_claiming_eligibility():
    result = analyze_finance(FinancialAnalysisRequest(
        available_margin_capital=1_000_000,
        loan={"annual_interest_rate": 10.5, "tenure_months": 120},
    ))
    assert result.calculated_project_cost == 10_000_000
    assert result.actual_modeled_loan == 9_000_000
    assert result.financial_status.value == "SUPPORTED"
    assert "user-supplied" in result.assumptions[1]
