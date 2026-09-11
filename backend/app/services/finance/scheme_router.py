"""Curated government scheme rules used by the public financial-roadmap API.

This module intentionally contains no lender quotations, market-cost assumptions, or
eligibility decisions. The published scheme terms are reviewed against the linked
government sources on the date carried by every route.
"""

from math import ceil

from app.schemas.finance import (
    CashflowAssessment,
    FinancialAssessment,
    FinancialRoadmapRequest,
    FinancialRoadmapResponse,
    GovernmentSchemeRoute,
)


VERIFIED_ON = "2026-09-10"
NSFDC_URL = "https://nsfdc.nic.in/faqs"
MUDRA_URL = "https://financialservices.gov.in/pradhan-mantri-mudra-yojana-pmmy"
PMEGP_URL = "https://www.kviconline.gov.in/pmegpeportal/dashboard/notification/Revised_PMEGP_Scheme_Guidelines_07122023_compressed.pdf"
PMFME_URL = "https://pmfme.mofpi.gov.in/pmfme/"
VISHWAKARMA_URL = "https://pmvishwakarma.gov.in/"
UDYAM_URL = "https://udyamregistration.gov.in/"


def _amortized_payment(principal: float, annual_rate: float, periods: int, periods_per_year: int) -> float:
    if principal <= 0 or periods <= 0:
        return 0.0
    periodic_rate = annual_rate / periods_per_year
    if periodic_rate == 0:
        return principal / periods
    return principal * periodic_rate * (1 + periodic_rate) ** periods / ((1 + periodic_rate) ** periods - 1)


def _nsfdc_assessment(margin: float) -> FinancialAssessment:
    project_cost = margin / 0.10
    requested_loan = project_cost * 0.90
    base = {
        "margin_capital": margin,
        "project_cost": project_cost,
        "requested_loan": requested_loan,
        "repayment_frequency_note": "NSFDC publishes quarterly instalments for Micro Finance. Term Loan frequency must be confirmed with the channelizing agency; the quarterly figure is a planning illustration.",
        "calculation_limitations": [
            "This is a planning model using a 10% margin, not a credit sanction or entitlement.",
            "The illustration starts repayment after the published moratorium and does not capitalize moratorium interest.",
            "NSFDC eligibility, project viability, documents and the final repayment schedule are determined by its authorized channelizing agency.",
        ],
    }
    if project_cost <= 140_000:
        scheme_name, loan_cap, rate, tenure, moratorium = "NSFDC Micro Finance Scheme", 125_000, 0.065, 36, 3
    elif project_cost <= 5_000_000:
        scheme_name, loan_cap, rate, tenure, moratorium = "NSFDC Term Loan", 4_500_000, 0.08, 84, 6
    else:
        return FinancialAssessment(
            status="OUTSIDE_BASELINE_RANGE",
            message="The calculated project cost exceeds the ₹50 lakh NSFDC Term Loan project-cost range used by this baseline.",
            eligible_loan=None,
            required_own_contribution=None,
            scheme_name=None,
            annual_interest_rate=None,
            tenure_months=None,
            moratorium_months=None,
            repayment_months=None,
            repayment_quarters=None,
            estimated_monthly_instalment=None,
            estimated_quarterly_instalment=None,
            estimated_total_repayment=None,
            estimated_total_interest=None,
            **base,
        )

    eligible_loan = min(requested_loan, loan_cap)
    repayment_months = tenure - moratorium
    repayment_quarters = ceil(repayment_months / 3)
    monthly_payment = _amortized_payment(eligible_loan, rate, repayment_months, 12)
    quarterly_payment = _amortized_payment(eligible_loan, rate, repayment_quarters, 4)
    total_repayment = quarterly_payment * repayment_quarters
    return FinancialAssessment(
        status="VALID",
        eligible_loan=eligible_loan,
        required_own_contribution=project_cost - eligible_loan,
        scheme_name=scheme_name,
        annual_interest_rate=rate,
        tenure_months=tenure,
        moratorium_months=moratorium,
        repayment_months=repayment_months,
        repayment_quarters=repayment_quarters,
        estimated_monthly_instalment=monthly_payment,
        estimated_quarterly_instalment=quarterly_payment,
        estimated_total_repayment=total_repayment,
        estimated_total_interest=total_repayment - eligible_loan,
        **base,
    )


def _nsfdc_route(assessment: FinancialAssessment) -> GovernmentSchemeRoute:
    return GovernmentSchemeRoute(
        code="NSFDC",
        name=assessment.scheme_name or "NSFDC concessional credit",
        administering_body="National Scheduled Castes Finance and Development Corporation",
        status="ELIGIBILITY_CHECK" if assessment.status == "VALID" else "NOT_APPLICABLE",
        summary="Published concessional-credit terms used as the baseline financial illustration." if assessment.status == "VALID" else "The project-cost baseline is above the published Term Loan project-cost range.",
        official_url=NSFDC_URL,
        source_verified_on=VERIFIED_ON,
        funding_limit=assessment.eligible_loan,
        beneficiary_interest_rate=assessment.annual_interest_rate,
        tenure_months=assessment.tenure_months,
        moratorium_months=assessment.moratorium_months,
        estimated_monthly_instalment=assessment.estimated_monthly_instalment,
        estimated_quarterly_instalment=assessment.estimated_quarterly_instalment,
        conditions=[
            "Applicant must satisfy NSFDC’s Scheduled Caste certificate and annual-family-income conditions.",
            "Application is routed through an authorized State/Channelizing Agency or the official PM-SURAJ channel.",
            "The activity must be legal, viable and accepted by the implementing agency.",
        ],
        limitations=assessment.calculation_limitations,
    )


def _mudra_route(request: FinancialRoadmapRequest, assessment: FinancialAssessment) -> GovernmentSchemeRoute:
    loan_need = assessment.requested_loan
    if loan_need <= 50_000:
        category, cap, condition = "Shishu", 50_000, None
    elif loan_need <= 500_000:
        category, cap, condition = "Kishore", 500_000, None
    elif loan_need <= 1_000_000:
        category, cap, condition = "Tarun", 1_000_000, None
    elif loan_need <= 2_000_000:
        category, cap, condition = "Tarun Plus", 2_000_000, "Tarun Plus is only for entrepreneurs who have availed and successfully repaid a previous Tarun loan."
    else:
        return GovernmentSchemeRoute(
            code="PMMY",
            name="Pradhan Mantri MUDRA Yojana (PMMY)",
            administering_body="Department of Financial Services, Ministry of Finance",
            status="NOT_APPLICABLE",
            summary="The stated loan need exceeds the published ₹20 lakh Tarun Plus ceiling.",
            official_url=MUDRA_URL,
            source_verified_on=VERIFIED_ON,
            conditions=[],
            limitations=["PMMY interest rate, tenure and lender appraisal are not standardized on the Department of Financial Services scheme page."],
        )

    conditions = [
        "Institutional collateral-free credit is intended for eligible micro-enterprise activities, including term-loan and working-capital requirements.",
        f"The requested financing falls in the {category} published category (up to ₹{cap:,.0f}).",
    ]
    status = "LENDER_TERMS_REQUIRED"
    if condition:
        conditions.append(condition)
        if not request.has_repaid_mudra_tarun:
            status = "ELIGIBILITY_CHECK"
    return GovernmentSchemeRoute(
        code="PMMY",
        name=f"Pradhan Mantri MUDRA Yojana — {category}",
        administering_body="Department of Financial Services, Ministry of Finance",
        status=status,
        summary="A government-published credit category is available for this loan size; its rate, tenure and instalment are set by the participating lender.",
        official_url=MUDRA_URL,
        source_verified_on=VERIFIED_ON,
        funding_limit=cap,
        conditions=conditions,
        limitations=["No PMMY EMI is calculated because the official scheme page does not publish one borrower rate or tenure for all lenders."],
    )


def _pmegp_route(request: FinancialRoadmapRequest, assessment: FinancialAssessment) -> GovernmentSchemeRoute:
    if request.activity_type == "not_sure" or request.activity_type == "traditional_artisan":
        return GovernmentSchemeRoute(
            code="PMEGP",
            name="Prime Minister's Employment Generation Programme (PMEGP)",
            administering_body="Khadi and Village Industries Commission",
            status="PROFILE_NEEDED",
            summary="Choose business/service or manufacturing before the applicable published project-cost ceiling can be checked.",
            official_url=PMEGP_URL,
            source_verified_on=VERIFIED_ON,
            conditions=["PMEGP supports new micro enterprises subject to its eligibility and activity rules."],
            limitations=["No subsidy is calculated until the activity, project location and PMEGP beneficiary group are self-declared."],
        )

    is_service = request.activity_type == "service_or_trading"
    project_cap = 2_000_000 if is_service else 5_000_000
    activity_label = "business/service" if is_service else "manufacturing / food processing"
    if assessment.project_cost > project_cap:
        return GovernmentSchemeRoute(
            code="PMEGP",
            name="Prime Minister's Employment Generation Programme (PMEGP)",
            administering_body="Khadi and Village Industries Commission",
            status="NOT_APPLICABLE",
            summary=f"The calculated project cost is above the published ₹{project_cap:,.0f} subsidy-eligible ceiling for {activity_label} projects.",
            official_url=PMEGP_URL,
            source_verified_on=VERIFIED_ON,
            funding_limit=project_cap,
            conditions=["The final activity classification and eligibility are determined under PMEGP guidelines."],
            limitations=["The published ceiling is for subsidy eligibility and does not constitute sanction."],
        )

    conditions = [
        f"Published project-cost ceiling for this selected {activity_label} profile: ₹{project_cap:,.0f}.",
        "The final activity, new-unit eligibility, education/training and bank appraisal must be confirmed through the official PMEGP process.",
    ]
    if request.area_type == "not_sure" or request.pmegp_beneficiary_group == "not_sure":
        return GovernmentSchemeRoute(
            code="PMEGP",
            name="Prime Minister's Employment Generation Programme (PMEGP)",
            administering_body="Khadi and Village Industries Commission",
            status="PROFILE_NEEDED",
            summary="The project is within the published activity ceiling. Select operating area and beneficiary group to see the official margin-money rate.",
            official_url=PMEGP_URL,
            source_verified_on=VERIFIED_ON,
            funding_limit=project_cap,
            conditions=conditions,
            limitations=["No PMEGP subsidy is assumed until the user self-declares the published calculation inputs and eligibility is verified."],
        )

    special = request.pmegp_beneficiary_group == "special"
    rural = request.area_type == "rural"
    contribution_rate = 0.05 if special else 0.10
    subsidy_rate = 0.35 if special and rural else 0.25 if special or rural else 0.15
    subsidy = assessment.project_cost * subsidy_rate
    group = "special category" if special else "general category"
    conditions.extend([
        f"Self-declared PMEGP calculation profile: {group}, {request.area_type} project location.",
        f"Published beneficiary contribution: {contribution_rate * 100:.0f}%; published margin-money subsidy: {subsidy_rate * 100:.0f}% of project cost.",
    ])
    return GovernmentSchemeRoute(
        code="PMEGP",
        name="Prime Minister's Employment Generation Programme (PMEGP)",
        administering_body="Khadi and Village Industries Commission",
        status="ELIGIBILITY_CHECK",
        summary="Published PMEGP contribution and margin-money rates are calculated from your self-declared profile; final approval remains with the implementing agency and bank.",
        official_url=PMEGP_URL,
        source_verified_on=VERIFIED_ON,
        funding_limit=project_cap,
        potential_subsidy=subsidy,
        minimum_beneficiary_contribution=assessment.project_cost * contribution_rate,
        conditions=conditions,
        limitations=["Margin money is not cash paid upfront to the beneficiary. Loan disbursement, lock-in and final bank finance must be confirmed with the official agency/bank."],
    )


def _pmfme_route(request: FinancialRoadmapRequest, assessment: FinancialAssessment) -> GovernmentSchemeRoute:
    if request.activity_type != "food_processing":
        return GovernmentSchemeRoute(
            code="PMFME",
            name="PM Formalisation of Micro Food Processing Enterprises (PMFME)",
            administering_body="Ministry of Food Processing Industries",
            status="NOT_APPLICABLE",
            summary="PMFME is shown only for a food-processing enterprise profile.",
            official_url=PMFME_URL,
            source_verified_on=VERIFIED_ON,
            conditions=[],
            limitations=[],
        )
    subsidy = min(assessment.project_cost * 0.35, 1_000_000)
    return GovernmentSchemeRoute(
        code="PMFME",
        name="PM Formalisation of Micro Food Processing Enterprises (PMFME)",
        administering_body="Ministry of Food Processing Industries",
        status="AVAILABILITY_CHECK",
        summary="The published individual-unit grant rule produces a potential credit-linked capital-subsidy illustration. Confirm current application availability, ODOP priority and activity eligibility before relying on it.",
        official_url=PMFME_URL,
        source_verified_on=VERIFIED_ON,
        potential_subsidy=subsidy,
        minimum_beneficiary_contribution=assessment.project_cost * 0.10,
        conditions=[
            "Published individual-unit support: 35% credit-linked capital subsidy, capped at ₹10 lakh per unit.",
            "Published minimum beneficiary contribution: 10%; the balance is subject to bank loan sanction and scheme conditions.",
            "Food-safety registration, the applicable food-processing activity and local ODOP guidance must be verified.",
        ],
        limitations=["No PMFME loan or EMI is calculated because bank terms and current component availability require official confirmation."],
    )


def _vishwakarma_route(request: FinancialRoadmapRequest) -> GovernmentSchemeRoute:
    if request.activity_type != "traditional_artisan":
        return GovernmentSchemeRoute(
            code="PMV",
            name="PM Vishwakarma",
            administering_body="Ministry of Micro, Small and Medium Enterprises",
            status="NOT_APPLICABLE",
            summary="This route is reserved for an eligible traditional artisan/craftsperson trade.",
            official_url=VISHWAKARMA_URL,
            source_verified_on=VERIFIED_ON,
            conditions=[],
            limitations=[],
        )
    if request.vishwakarma_loan_stage == "not_confirmed":
        return GovernmentSchemeRoute(
            code="PMV",
            name="PM Vishwakarma",
            administering_body="Ministry of Micro, Small and Medium Enterprises",
            status="PROFILE_NEEDED",
            summary="Confirm whether you are preparing for the first or second published loan tranche after verifying the eligible trade and programme requirements.",
            official_url=VISHWAKARMA_URL,
            source_verified_on=VERIFIED_ON,
            conditions=["The scheme is for the published traditional trades and requires programme verification."],
            limitations=["No tranche or repayment estimate is shown before the user identifies the applicable loan stage."],
        )
    second = request.vishwakarma_loan_stage == "second"
    principal, tenure = (200_000, 30) if second else (100_000, 18)
    payment = _amortized_payment(principal, 0.05, tenure, 12)
    conditions = [
        "Beneficiary interest published for the enterprise loan: 5% per annum.",
        "First tranche requires successful completion of basic training; second tranche has additional successful-repayment and programme conditions.",
    ]
    return GovernmentSchemeRoute(
        code="PMV",
        name=f"PM Vishwakarma — {'second' if second else 'first'} loan tranche",
        administering_body="Ministry of Micro, Small and Medium Enterprises",
        status="ELIGIBILITY_CHECK",
        summary="A published tranche and 5% beneficiary-rate instalment are illustrated for the selected stage; programme verification is still required.",
        official_url=VISHWAKARMA_URL,
        source_verified_on=VERIFIED_ON,
        funding_limit=principal,
        beneficiary_interest_rate=0.05,
        tenure_months=tenure,
        estimated_monthly_instalment=payment,
        conditions=conditions,
        limitations=["The estimate uses standard monthly amortization. The published scheme terms do not provide a blanket moratorium rule for this illustration."],
    )


def _cashflow(request: FinancialRoadmapRequest, assessment: FinancialAssessment) -> CashflowAssessment:
    limitations = ["No government default has been used for rent, wages, stock, utilities, transport or sales. Every amount below is supplied by the user."]
    costs_available = request.monthly_fixed_cost is not None and request.monthly_variable_cost is not None
    reserve_available = costs_available and request.operating_reserve_months is not None
    revenue_available = request.expected_monthly_revenue is not None
    if not costs_available:
        limitations.append("Enter both monthly fixed and variable operating costs to calculate the operating-cost total.")
    if not reserve_available:
        limitations.append("Enter a user-chosen number of reserve months to calculate a working-capital reserve.")
    if not revenue_available:
        limitations.append("Enter expected monthly revenue to view cash before and after the baseline instalment.")
    operating_cost = (request.monthly_fixed_cost or 0) + (request.monthly_variable_cost or 0) if costs_available else None
    before_debt = request.expected_monthly_revenue - operating_cost if revenue_available and operating_cost is not None else None
    after_debt = before_debt - assessment.estimated_monthly_instalment if before_debt is not None and assessment.estimated_monthly_instalment is not None else None
    reserve = operating_cost * request.operating_reserve_months if reserve_available and operating_cost is not None and request.operating_reserve_months is not None else None
    return CashflowAssessment(
        status="AVAILABLE" if costs_available and reserve_available and revenue_available else "INCOMPLETE",
        monthly_operating_cost=operating_cost,
        monthly_cash_before_debt=before_debt,
        monthly_cash_after_baseline_instalment=after_debt,
        operating_reserve_requirement=reserve,
        limitations=limitations,
    )


def build_financial_roadmap(request: FinancialRoadmapRequest) -> FinancialRoadmapResponse:
    assessment = _nsfdc_assessment(request.margin_capital)
    routes = [
        _nsfdc_route(assessment),
        _mudra_route(request, assessment),
        _pmegp_route(request, assessment),
        _pmfme_route(request, assessment),
        _vishwakarma_route(request),
    ]
    cashflow = _cashflow(request, assessment)
    return FinancialRoadmapResponse(
        assessment=assessment,
        cashflow=cashflow,
        routes=routes,
        readiness_actions=[
            "Prepare a project report that separates capital expenditure from working-capital needs and attaches current supplier quotations.",
            "Use only the official Udyam Registration portal for enterprise registration: " + UDYAM_URL,
            "Confirm the selected scheme’s applicant eligibility, activity classification, documents, training and final repayment schedule through its official channel.",
            "Do not pay intermediaries for a government-scheme sanction; use the official application links shown for each route.",
        ],
        data_status="VERIFIED_GOVERNMENT_RULES",
        data_limitations=[
            "The service uses a manually curated government-rule registry because the listed schemes do not expose one common public calculation API.",
            "All lending decisions, rates not explicitly published by a scheme, scheme availability and sanctions remain outside this tool.",
            "Government scheme rules can change. Each route displays its source and review date for confirmation before an application.",
        ],
    )
