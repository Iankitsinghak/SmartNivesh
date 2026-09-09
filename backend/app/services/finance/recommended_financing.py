from app.schemas.finance import RecommendedFinancing
from typing import Optional

def calculate_recommended_financing(
    project_cost: float,
    margin_percentage: float,
    base_profit: Optional[float],
    conservative_profit: Optional[float],
    monthly_emi: float,
    loan_amount: float
) -> RecommendedFinancing:
    """
    Recommends financing structure. 
    Does not exceed the requested loan amount. Flags risk if coverage is too low.
    """
    if conservative_profit is None or base_profit is None or monthly_emi <= 0:
        return RecommendedFinancing(
            requested_project_cost=project_cost,
            recommended_project_cost=project_cost,
            required_margin=project_cost * margin_percentage,
            recommended_loan=loan_amount,
            monthly_emi=monthly_emi,
            base_repayment_coverage=round(base_profit / monthly_emi, 2) if base_profit is not None and monthly_emi > 0 else None,
            conservative_repayment_coverage=None,
            financial_feasibility="UNKNOWN"
        )
        
    cons_coverage = conservative_profit / monthly_emi
    base_coverage = base_profit / monthly_emi
    
    feasibility = "FEASIBLE"
    recommended_loan = loan_amount
    recommended_project = project_cost
    
    if cons_coverage < 1.0:
        feasibility = "HIGH_RISK"
        # We could reduce the recommended loan here to make it viable, 
        # but determining the exact loan requires reverse calculating the EMI.
        # For this stage, we highlight the risk.
    
    return RecommendedFinancing(
        requested_project_cost=project_cost,
        recommended_project_cost=recommended_project,
        required_margin=recommended_project * margin_percentage,
        recommended_loan=recommended_loan,
        monthly_emi=monthly_emi,
        base_repayment_coverage=round(base_coverage, 2),
        conservative_repayment_coverage=round(cons_coverage, 2),
        financial_feasibility=feasibility
    )
