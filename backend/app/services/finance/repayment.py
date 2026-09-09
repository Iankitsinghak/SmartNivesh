from app.services.finance.emi import calculate_emi

def calculate_repayment(principal: float, annual_interest_rate: float, tenure_months: int):
    """
    Calculates total repayment and interest.
    """
    if principal < 0 or tenure_months <= 0:
        raise ValueError("Invalid loan principal or tenure")

    emi = calculate_emi(principal, annual_interest_rate, tenure_months)
    total_repayment = emi * tenure_months
    total_interest = total_repayment - principal
    
    # Handle minor float arithmetic issues where interest might be slightly negative due to rounding
    if total_interest < 0:
        total_interest = 0.0

    return {
        "monthly_emi": emi,
        "total_repayment": round(total_repayment, 2),
        "total_interest": round(total_interest, 2)
    }

def calculate_repayment_coverage(monthly_cash_available: float, emi: float):
    """
    Calculates Repayment Coverage ratio.
    """
    if emi <= 0:
        return None
    return round(monthly_cash_available / emi, 2)
