from typing import List
from app.schemas.finance import FinancialAnalysisRequest, FinancialAnalysisResponse, RepaymentScheduleRow
from app.core.enums import FinancialStatus, FinancingBand
from app.utils.provenance import DataClassification, ConfidenceLevel
from app.schemas.common import DataProvenance
from app.services.finance.loan_engine import (
    derive_project_cost,
    derive_loan_requirement,
    determine_financing_band
)
from app.services.finance.emi import calculate_deterministic_emi
from app.services.finance.repayment import generate_amortization_schedule

def analyze_finance(request: FinancialAnalysisRequest) -> FinancialAnalysisResponse:
    margin = request.available_margin_capital

    if margin <= 0:
        return FinancialAnalysisResponse(
            available_margin_capital=margin,
            calculated_project_cost=0.0,
            calculated_loan_requirement=0.0,
            applicable_financing_band=FinancingBand.UNSUPPORTED,
            actual_modeled_loan=0.0,
            financing_gap=0.0,
            monthly_emi=0.0,
            total_repayment=0.0,
            total_interest=0.0,
            repayment_schedule=[],
            financial_status=FinancialStatus.INVALID_INPUT
        )

    # 1. Project Cost & Loan Requirement
    project_cost = derive_project_cost(margin)
    loan_requirement = derive_loan_requirement(project_cost)

    # 2. Determine Financing Band
    band, params = determine_financing_band(project_cost)

    if band == FinancingBand.UNSUPPORTED:
        return FinancialAnalysisResponse(
            available_margin_capital=margin,
            calculated_project_cost=project_cost,
            calculated_loan_requirement=loan_requirement,
            applicable_financing_band=band,
            actual_modeled_loan=0.0,
            financing_gap=loan_requirement,
            monthly_emi=0.0,
            total_repayment=0.0,
            total_interest=0.0,
            repayment_schedule=[],
            financial_status=FinancialStatus.PROJECT_RANGE_EXCEEDED
        )

    # Extract parameters
    interest_rate = params.get("interest_rate", 0.0)
    tenure_months = params.get("tenure_months", 0)
    moratorium_months = params.get("moratorium_months", 0)
    max_agency_loan = params.get("maximum_agency_loan", 0.0)

    # 3. Loan Cap Logic
    if loan_requirement > max_agency_loan:
        actual_modeled_loan = max_agency_loan
        financing_gap = round(loan_requirement - actual_modeled_loan, 2)
        status = FinancialStatus.LOAN_CAP_EXCEEDED
    else:
        actual_modeled_loan = loan_requirement
        financing_gap = 0.0
        status = FinancialStatus.SUPPORTED

    # 4. EMI & Repayment
    monthly_emi = calculate_deterministic_emi(
        principal=actual_modeled_loan, 
        annual_interest_rate=interest_rate, 
        tenure_months=tenure_months
    )

    schedule = generate_amortization_schedule(
        principal=actual_modeled_loan,
        annual_interest_rate=interest_rate,
        tenure_months=tenure_months,
        monthly_emi=monthly_emi
    )

    total_repayment = round(sum(row.payment for row in schedule), 2)
    total_interest = round(sum(row.interest_component for row in schedule), 2)

    # 5. Provenance
    provenance = [
        DataProvenance(
            source_id="problem_statement",
            source_name="Vyapar Sath Financial Rules",
            data_type=DataClassification.VERIFIED,
            confidence=ConfidenceLevel.HIGH
        )
    ]

    return FinancialAnalysisResponse(
        available_margin_capital=margin,
        calculated_project_cost=project_cost,
        calculated_loan_requirement=loan_requirement,
        applicable_financing_band=band,
        interest_rate=interest_rate,
        tenure_months=tenure_months,
        moratorium_months=moratorium_months,
        maximum_agency_loan=max_agency_loan,
        actual_modeled_loan=actual_modeled_loan,
        financing_gap=financing_gap,
        monthly_emi=monthly_emi,
        total_repayment=total_repayment,
        total_interest=total_interest,
        repayment_schedule=schedule,
        financial_status=status,
        data_classification=DataClassification.CALCULATED,
        provenance=provenance
    )
