def calculate_deterministic_emi(principal: float, annual_interest_rate: float, tenure_months: int) -> float:
    """
    Calculates deterministic EMI.
    Formula: P * r * (1+r)^n / ((1+r)^n - 1)
    Where:
    P = Principal
    r = Monthly interest rate (annual / 12 / 100)
    n = Number of monthly installments
    """
    if principal <= 0 or tenure_months <= 0:
        return 0.0

    if annual_interest_rate <= 0:
        # Zero interest case
        return round(principal / tenure_months, 2)

    r = (annual_interest_rate / 12.0) / 100.0
    n = tenure_months

    factor = (1 + r) ** n
    emi = principal * r * factor / (factor - 1)

    return round(emi, 2)
