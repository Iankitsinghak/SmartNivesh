from app.schemas.scheme import SchemeRoutingRequest, SchemeRoutingResponse
from app.core.enums import FinancingBand, EligibilityStatus
from app.core.constants import SCHEME_CONFIG_MICRO_FINANCE, SCHEME_CONFIG_TERM_LOAN

def determine_scheme_applicability(request: SchemeRoutingRequest) -> SchemeRoutingResponse:
    """
    Deterministically routes the financial assessment to a specific scheme.
    Does NOT recalculate project cost or loan requirements. Uses values supplied by the Financial Engine.
    """
    
    if request.project_cost <= 0 or request.loan_requirement < 0:
        return _build_unsupported_response(
            request, 
            rule_status="INVALID_FINANCIALS"
        )
        
    if request.financing_band == FinancingBand.UNSUPPORTED:
        return _build_unsupported_response(
            request, 
            rule_status="PROJECT_RANGE_EXCEEDED"
        )
        
    # Route to appropriate scheme based on band
    if request.financing_band == FinancingBand.MICRO_FINANCE:
        config = SCHEME_CONFIG_MICRO_FINANCE
    elif request.financing_band == FinancingBand.TERM_LOAN:
        config = SCHEME_CONFIG_TERM_LOAN
    else:
        return _build_unsupported_response(
            request, 
            rule_status="UNKNOWN_BAND"
        )
        
    # Final check: is the project cost truly within the scheme's allowed range?
    if request.project_cost > config["max_project_cost"]:
        return _build_unsupported_response(
            request,
            rule_status="PROJECT_RANGE_EXCEEDED"
        )

    return SchemeRoutingResponse(
        scheme_code=config["scheme_code"],
        scheme_name=config["name"],
        applicable=True,
        project_cost=request.project_cost,
        loan_requirement=request.loan_requirement,
        maximum_loan=config["maximum_loan"],
        interest_rate=config["interest_rate"],
        tenure_years=config["tenure_years"],
        moratorium_months=config["moratorium_months"],
        financing_percentage=config["financing_percentage"],
        loan_cap_exceeded=request.financing_gap > 0,
        financing_gap=request.financing_gap,
        eligibility_status=EligibilityStatus.PENDING,
        missing_eligibility_inputs=["beneficiary_age", "domicile_status", "educational_qualification", "family_income"],
        rule_status="SCHEME_APPLICABLE"
    )

def _build_unsupported_response(request: SchemeRoutingRequest, rule_status: str) -> SchemeRoutingResponse:
    return SchemeRoutingResponse(
        scheme_code=None,
        scheme_name=None,
        applicable=False,
        project_cost=request.project_cost,
        loan_requirement=request.loan_requirement,
        maximum_loan=None,
        interest_rate=None,
        tenure_years=None,
        moratorium_months=None,
        financing_percentage=None,
        loan_cap_exceeded=False,
        financing_gap=request.financing_gap,
        eligibility_status=EligibilityStatus.INSUFFICIENT_INFORMATION,
        missing_eligibility_inputs=[],
        rule_status=rule_status
    )
