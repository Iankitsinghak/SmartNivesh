from app.schemas.finance import FinancialRoadmapRequest
from app.services.finance.scheme_router import build_financial_roadmap


def routes_for(response, code):
    return next(route for route in response.routes if route.code == code)


def test_nsfdc_micro_finance_uses_published_cap_and_quarterly_plan():
    response = build_financial_roadmap(FinancialRoadmapRequest(margin_capital=10_000))
    assessment = response.assessment
    assert assessment.project_cost == 100_000
    assert assessment.requested_loan == 90_000
    assert assessment.scheme_name == "NSFDC Micro Finance Scheme"
    assert assessment.eligible_loan == 90_000
    assert assessment.repayment_quarters == 11
    assert assessment.estimated_quarterly_instalment is not None
    assert routes_for(response, "NSFDC").status == "ELIGIBILITY_CHECK"


def test_nsfdc_term_loan_applies_published_loan_cap():
    response = build_financial_roadmap(FinancialRoadmapRequest(margin_capital=500_000))
    assessment = response.assessment
    assert assessment.project_cost == 5_000_000
    assert assessment.requested_loan == 4_500_000
    assert assessment.scheme_name == "NSFDC Term Loan"
    assert assessment.eligible_loan == 4_500_000
    assert assessment.repayment_months == 78


def test_mudra_tarun_plus_requires_previous_tarun_repayment():
    response = build_financial_roadmap(FinancialRoadmapRequest(margin_capital=200_000))
    mudra = routes_for(response, "PMMY")
    assert mudra.name.endswith("Tarun Plus")
    assert mudra.status == "ELIGIBILITY_CHECK"
    assert mudra.estimated_monthly_instalment is None


def test_pmegp_uses_self_declared_rural_special_rates_only_when_complete():
    incomplete = build_financial_roadmap(FinancialRoadmapRequest(margin_capital=100_000, activity_type="service_or_trading"))
    assert routes_for(incomplete, "PMEGP").status == "PROFILE_NEEDED"

    response = build_financial_roadmap(FinancialRoadmapRequest(
        margin_capital=100_000,
        activity_type="service_or_trading",
        area_type="rural",
        pmegp_beneficiary_group="special",
    ))
    pmegp = routes_for(response, "PMEGP")
    assert pmegp.status == "ELIGIBILITY_CHECK"
    assert pmegp.minimum_beneficiary_contribution == 50_000
    assert pmegp.potential_subsidy == 350_000


def test_pmfme_and_cashflow_use_only_explicit_inputs():
    response = build_financial_roadmap(FinancialRoadmapRequest(
        margin_capital=100_000,
        activity_type="food_processing",
        monthly_fixed_cost=12_000,
        monthly_variable_cost=8_000,
        expected_monthly_revenue=45_000,
        operating_reserve_months=2,
    ))
    pmfme = routes_for(response, "PMFME")
    assert pmfme.status == "AVAILABILITY_CHECK"
    assert pmfme.potential_subsidy == 350_000
    assert response.cashflow.status == "AVAILABLE"
    assert response.cashflow.monthly_operating_cost == 20_000
    assert response.cashflow.operating_reserve_requirement == 40_000
