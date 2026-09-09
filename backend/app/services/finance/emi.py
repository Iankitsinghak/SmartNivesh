def calculate_emi(principal: float, annual_interest_rate: float, tenure_months: int) -> float:
    """
    Standard EMI calculation.
    """
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    
    if annual_interest_rate <= 0:
        return round(principal / tenure_months, 2)
        
    monthly_rate = annual_interest_rate / 12.0 / 100.0
    factor = (1 + monthly_rate) ** tenure_months
    emi = principal * monthly_rate * factor / (factor - 1)
    
    return round(emi, 2)
