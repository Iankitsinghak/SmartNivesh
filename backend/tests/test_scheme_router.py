import pytest
from app.schemas.scheme import SchemeRoutingRequest
from app.core.enums import FinancingBand, EligibilityStatus
from app.services.schemes.scheme_router import determine_scheme_applicability

def test_micro_finance_routing():
    request = SchemeRoutingRequest(
        project_cost=100000.0,
        loan_requirement=90000.0,
        financing_band=FinancingBand.MICRO_FINANCE,
        actual_modeled_loan=90000.0,
        financing_gap=0.0
    )
    result = determine_scheme_applicability(request)
    assert result.scheme_code == "MF-01"
    assert result.applicable is True
    assert result.eligibility_status == EligibilityStatus.PENDING

def test_term_loan_routing():
    request = SchemeRoutingRequest(
        project_cost=1000000.0,
        loan_requirement=900000.0,
        financing_band=FinancingBand.TERM_LOAN,
        actual_modeled_loan=900000.0,
        financing_gap=0.0
    )
    result = determine_scheme_applicability(request)
    assert result.scheme_code == "TL-01"
    assert result.applicable is True

def test_exact_1_4_boundary():
    request = SchemeRoutingRequest(
        project_cost=140000.0,
        loan_requirement=126000.0,
        financing_band=FinancingBand.MICRO_FINANCE,
        actual_modeled_loan=125000.0,
        financing_gap=1000.0
    )
    result = determine_scheme_applicability(request)
    assert result.scheme_code == "MF-01"
    assert result.applicable is True

def test_just_above_1_4_boundary():
    request = SchemeRoutingRequest(
        project_cost=140001.0,
        loan_requirement=126000.9,
        financing_band=FinancingBand.TERM_LOAN,
        actual_modeled_loan=126000.9,
        financing_gap=0.0
    )
    result = determine_scheme_applicability(request)
    assert result.scheme_code == "TL-01"
    assert result.applicable is True

def test_exact_50_boundary():
    request = SchemeRoutingRequest(
        project_cost=5000000.0,
        loan_requirement=4500000.0,
        financing_band=FinancingBand.TERM_LOAN,
        actual_modeled_loan=4500000.0,
        financing_gap=0.0
    )
    result = determine_scheme_applicability(request)
    assert result.scheme_code == "TL-01"
    assert result.applicable is True

def test_above_50_boundary():
    request = SchemeRoutingRequest(
        project_cost=5000001.0,
        loan_requirement=4500000.9,
        financing_band=FinancingBand.UNSUPPORTED,
        actual_modeled_loan=0.0,
        financing_gap=4500000.9
    )
    result = determine_scheme_applicability(request)
    assert result.scheme_code is None
    assert result.applicable is False
    assert result.rule_status == "PROJECT_RANGE_EXCEEDED"

def test_micro_loan_cap():
    request = SchemeRoutingRequest(
        project_cost=140000.0,
        loan_requirement=126000.0,
        financing_band=FinancingBand.MICRO_FINANCE,
        actual_modeled_loan=125000.0,
        financing_gap=1000.0
    )
    result = determine_scheme_applicability(request)
    assert result.loan_cap_exceeded is True
    assert result.financing_gap == 1000.0

def test_term_loan_cap():
    # Theoretically if 90% of some allowed cost was > 45L. But max cost is 50L.
    # We can pass an artificial gap to ensure pass-through
    request = SchemeRoutingRequest(
        project_cost=5000000.0,
        loan_requirement=4600000.0, # artificial
        financing_band=FinancingBand.TERM_LOAN,
        actual_modeled_loan=4500000.0,
        financing_gap=100000.0
    )
    result = determine_scheme_applicability(request)
    assert result.loan_cap_exceeded is True
    assert result.financing_gap == 100000.0

def test_financing_gap():
    request = SchemeRoutingRequest(
        project_cost=140000.0,
        loan_requirement=126000.0,
        financing_band=FinancingBand.MICRO_FINANCE,
        actual_modeled_loan=125000.0,
        financing_gap=1000.0
    )
    result = determine_scheme_applicability(request)
    assert result.financing_gap == 1000.0

def test_eligibility_separate():
    request = SchemeRoutingRequest(
        project_cost=100000.0,
        loan_requirement=90000.0,
        financing_band=FinancingBand.MICRO_FINANCE,
        actual_modeled_loan=90000.0,
        financing_gap=0.0
    )
    result = determine_scheme_applicability(request)
    assert result.applicable is True
    assert result.eligibility_status == EligibilityStatus.PENDING

def test_invalid_input_handling():
    request = SchemeRoutingRequest(
        project_cost=-10.0,
        loan_requirement=-9.0,
        financing_band=FinancingBand.MICRO_FINANCE,
        actual_modeled_loan=0.0,
        financing_gap=0.0
    )
    result = determine_scheme_applicability(request)
    assert result.applicable is False
    assert result.rule_status == "INVALID_FINANCIALS"

def test_deterministic_output():
    request1 = SchemeRoutingRequest(
        project_cost=100000.0,
        loan_requirement=90000.0,
        financing_band=FinancingBand.MICRO_FINANCE,
        actual_modeled_loan=90000.0,
        financing_gap=0.0
    )
    res1 = determine_scheme_applicability(request1)
    res2 = determine_scheme_applicability(request1)
    assert res1.model_dump() == res2.model_dump()
