from app.core.constants import (
    MICRO_FINANCE_MAX_COST,
    MICRO_FINANCE_INTEREST,
    MICRO_FINANCE_TENURE_MONTHS,
    MICRO_FINANCE_MORATORIUM,
    MICRO_FINANCE_MAX_LOAN,
    TERM_LOAN_MAX_COST,
    TERM_LOAN_INTEREST,
    TERM_LOAN_TENURE_MONTHS,
    TERM_LOAN_MORATORIUM,
    TERM_LOAN_MAX_LOAN,
)
from app.core.enums import FinancingBand

def derive_project_cost(margin_capital: float) -> float:
    """
    Project Cost = Available Margin Capital / 10%
    """
    return round(margin_capital * 10.0, 2)

def derive_loan_requirement(project_cost: float) -> float:
    """
    Loan Requirement = Project Cost * 90%
    """
    return round(project_cost * 0.90, 2)

def determine_financing_band(project_cost: float) -> tuple[FinancingBand, dict]:
    """
    Returns the applicable financing band and its parameters based on project cost.
    """
    if project_cost <= MICRO_FINANCE_MAX_COST:
        return FinancingBand.MICRO_FINANCE, {
            "interest_rate": MICRO_FINANCE_INTEREST,
            "tenure_months": MICRO_FINANCE_TENURE_MONTHS,
            "moratorium_months": MICRO_FINANCE_MORATORIUM,
            "maximum_agency_loan": MICRO_FINANCE_MAX_LOAN
        }
    elif project_cost <= TERM_LOAN_MAX_COST:
        return FinancingBand.TERM_LOAN, {
            "interest_rate": TERM_LOAN_INTEREST,
            "tenure_months": TERM_LOAN_TENURE_MONTHS,
            "moratorium_months": TERM_LOAN_MORATORIUM,
            "maximum_agency_loan": TERM_LOAN_MAX_LOAN
        }
    else:
        return FinancingBand.UNSUPPORTED, {}
