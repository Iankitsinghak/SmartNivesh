import pytest
from app.services.finance.finance_engine import analyze_finance
from app.schemas.finance import FinancialAnalysisRequest
from app.core.enums import FinancialStatus, FinancingBand
from app.services.finance.emi import calculate_deterministic_emi

# --- Test 1 — Basic Micro Finance ---
def test_micro_finance_basic():
    # Capital = 10,000 -> Project Cost = 1,00,000 (within 1.4L limit)
    request = FinancialAnalysisRequest(available_margin_capital=10000.0)
    response = analyze_finance(request)

    assert response.calculated_project_cost == 100000.0
    assert response.calculated_loan_requirement == 90000.0
    assert response.applicable_financing_band == FinancingBand.MICRO_FINANCE
    assert response.interest_rate == 6.5
    assert response.tenure_months == 36
    assert response.moratorium_months == 3
    assert response.maximum_agency_loan == 125000.0
    assert response.actual_modeled_loan == 90000.0
    assert response.financing_gap == 0.0
    assert response.financial_status == FinancialStatus.SUPPORTED

# --- Test 2 — Term Loan ---
def test_term_loan_basic():
    # Capital = 1,00,000 -> Project Cost = 10,00,000
    request = FinancialAnalysisRequest(available_margin_capital=100000.0)
    response = analyze_finance(request)

    assert response.calculated_project_cost == 1000000.0
    assert response.calculated_loan_requirement == 900000.0
    assert response.applicable_financing_band == FinancingBand.TERM_LOAN
    assert response.interest_rate == 8.0
    assert response.tenure_months == 84
    assert response.moratorium_months == 6
    assert response.maximum_agency_loan == 4500000.0

    expected_emi = calculate_deterministic_emi(900000.0, 8.0, 84)
    assert response.monthly_emi == expected_emi

# --- Test 3 — Loan Cap ---
def test_loan_cap_exceeded():
    # Capital = 6,00,000 -> Project Cost = 60,00,000. Wait, Project cost limit is 50L.
    # To hit loan cap but stay under project cost limit: 
    # Term loan max project cost = 50,00,000
    # 90% of 50,00,000 = 45,00,000
    # Actually, if project cost is 50L, loan requirement is 45L which is exactly the max agency loan. 
    # Let's adjust TERM_LOAN_MAX_COST temporarily or just use a scenario where loan requirement > max agency loan
    # But wait, max agency loan is exactly 90% of max project cost for both schemes!
    # Term Loan max cost = 50L -> 90% = 45L. Max loan = 45L. So gap is never natively > 0 unless rules are violated.
    # Let's test a theoretical boundary. If we force max_agency_loan to be lower, or if we just test the branch by simulating an artificially high requirement.
    # Wait, the user specifically asked: "Create a case where calculated financing exceeds the scheme's maximum agency loan... Verify calculated requirement != actual modeled loan and financing_gap > 0"
    # Is it possible to have project cost <= 50L but loan requirement > 45L?
    # No, because 50L * 90% = 45L.
    # What about Micro Finance?
    # Max cost = 1,40,000 -> 90% = 1,26,000. Max agency loan = 1,25,000.
    # AH! 1.26L > 1.25L. Perfect!
    request = FinancialAnalysisRequest(available_margin_capital=14000.0)
    response = analyze_finance(request)

    assert response.calculated_project_cost == 140000.0
    assert response.calculated_loan_requirement == 126000.0
    assert response.actual_modeled_loan == 125000.0
    assert response.financing_gap == 1000.0
    assert response.financial_status == FinancialStatus.LOAN_CAP_EXCEEDED

# --- Test 4 — Project Cost Limit ---
def test_project_cost_limit_exceeded():
    # Capital = 6,00,000 -> Project Cost = 60,00,000 (> 50L limit)
    request = FinancialAnalysisRequest(available_margin_capital=600000.0)
    response = analyze_finance(request)

    assert response.calculated_project_cost == 6000000.0
    assert response.applicable_financing_band == FinancingBand.UNSUPPORTED
    assert response.financial_status == FinancialStatus.PROJECT_RANGE_EXCEEDED
    assert response.actual_modeled_loan == 0.0

# --- Test 5 — Zero Interest ---
def test_zero_interest():
    # Test emi.py directly for zero interest
    emi = calculate_deterministic_emi(100000.0, 0.0, 10)
    assert emi == 10000.0

from pydantic import ValidationError

# --- Test 6 — Invalid Capital ---
def test_invalid_capital():
    with pytest.raises(ValidationError):
        FinancialAnalysisRequest(available_margin_capital=0.0)
    
    with pytest.raises(ValidationError):
        FinancialAnalysisRequest(available_margin_capital=-500.0)

# --- Test 7 — Amortization ---
def test_amortization_schedule():
    request = FinancialAnalysisRequest(available_margin_capital=100000.0)
    response = analyze_finance(request)
    
    schedule = response.repayment_schedule
    assert len(schedule) == 84
    
    # Verify balance decreases
    assert schedule[0].closing_balance > schedule[-1].closing_balance
    
    # Final balance is exactly zero
    assert schedule[-1].closing_balance == 0.0
    
    # Principal + interest = payment
    for row in schedule:
        assert round(row.principal_component + row.interest_component, 2) == round(row.payment, 2)

# --- Test 8 — Determinism ---
def test_determinism():
    request1 = FinancialAnalysisRequest(available_margin_capital=50000.0)
    response1 = analyze_finance(request1)
    
    request2 = FinancialAnalysisRequest(available_margin_capital=50000.0)
    response2 = analyze_finance(request2)
    
    assert response1.model_dump() == response2.model_dump()
