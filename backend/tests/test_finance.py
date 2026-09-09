import pytest
from app.services.finance.emi import calculate_emi
from app.services.finance.loan_engine import calculate_project_cost, calculate_loan_amount
from app.services.finance.repayment import calculate_repayment, calculate_repayment_coverage
from app.services.finance.finance_engine import analyze_finance
from app.schemas.finance import FinancialAnalysisRequest, RevenueAssumptions, CostAssumptions, LoanAssumptions
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_project_cost_calculation():
    assert calculate_project_cost(100000, 0.10) == 1000000.0
    assert calculate_project_cost(0, 0.10) == 0.0
    with pytest.raises(ValueError):
        calculate_project_cost(-100, 0.10)

def test_loan_calculation():
    assert calculate_loan_amount(1000000, 0.10) == 900000.0

def test_emi_calculation():
    # P = 900000, r = 8% / 12 = 0.006666, n = 84 (7 years)
    emi = calculate_emi(900000, 8.0, 84)
    assert emi == 14027.59
    
    # Zero interest
    assert calculate_emi(900000, 0.0, 84) == round(900000/84, 2)
    
    # Invalid inputs
    assert calculate_emi(0, 8.0, 84) == 0.0
    assert calculate_emi(900000, 8.0, 0) == 0.0

def test_repayment_engine():
    res = calculate_repayment(900000, 8.0, 84)
    assert res["monthly_emi"] == 14027.59
    assert res["total_repayment"] == round(14027.59 * 84, 2)
    assert res["total_interest"] == round((14027.59 * 84) - 900000, 2)

def test_repayment_coverage():
    assert calculate_repayment_coverage(28000, 14000) == 2.0
    assert calculate_repayment_coverage(14000, 0) is None

def test_analyze_finance_orchestrator():
    req = FinancialAnalysisRequest(
        available_margin=100000,
        revenue_assumptions=RevenueAssumptions(units_per_month=1000, selling_price=50),
        cost_assumptions=CostAssumptions(variable_cost_ratio=0.5, fixed_costs_per_month=10000),
        loan_assumptions=LoanAssumptions(annual_interest_rate=8.0, tenure_months=84)
    )
    
    res = analyze_finance(req)
    assert res.project_cost.value == 1000000.0
    assert res.loan_amount.value == 900000.0
    
    # Revenue: 1000 * 50 = 50000
    assert res.base_scenario.revenue.value == 50000.0
    # Variable cost: 50000 * 0.5 = 25000
    assert res.base_scenario.variable_cost.value == 25000.0
    # Fixed cost = 10000
    assert res.base_scenario.fixed_cost.value == 10000.0
    # Profit: 50000 - 25000 - 10000 = 15000
    assert res.base_scenario.operating_profit.value == 15000.0
    
    assert res.feasibility_indicators.break_even_units.value == round(10000 / (50 - 25), 2)
    assert res.recommended_financing.monthly_emi == res.monthly_emi.value

def test_api_endpoint():
    payload = {
        "available_margin": 100000,
        "revenue_assumptions": {"units_per_month": 1000, "selling_price": 50},
        "cost_assumptions": {"variable_cost_ratio": 0.5, "fixed_costs_per_month": 10000},
        "loan_assumptions": {"annual_interest_rate": 8.0, "tenure_months": 84}
    }
    response = client.post("/api/finance/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_cost"]["value"] == 1000000.0
    assert data["loan_amount"]["value"] == 900000.0
    assert data["base_scenario"]["operating_profit"]["value"] == 15000.0
