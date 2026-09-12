from decimal import Decimal, ROUND_HALF_UP, localcontext


MONEY = Decimal("0.01")


def _decimal(value: object) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def calculate_deterministic_emi(principal: float, annual_interest_rate: float, tenure_months: int) -> float:
    """
    Calculates deterministic EMI.
    Formula: P * r * (1+r)^n / ((1+r)^n - 1)
    Where:
    P = Principal
    r = Monthly interest rate (annual / 12 / 100)
    n = Number of monthly installments
    """
    principal_value = _decimal(principal)
    rate_value = _decimal(annual_interest_rate)
    if principal_value < 0:
        raise ValueError("Principal cannot be negative.")
    if tenure_months <= 0:
        raise ValueError("Tenure must be greater than zero.")
    if rate_value < 0:
        raise ValueError("Annual interest rate cannot be negative.")
    if principal_value == 0:
        return 0.0

    if rate_value == 0:
        # Zero interest case
        return float((principal_value / Decimal(tenure_months)).quantize(MONEY, rounding=ROUND_HALF_UP))

    with localcontext() as context:
        context.prec = 34
        monthly_rate = rate_value / Decimal(12) / Decimal(100)
        factor = (Decimal(1) + monthly_rate) ** tenure_months
        emi = principal_value * monthly_rate * factor / (factor - Decimal(1))
    return float(emi.quantize(MONEY, rounding=ROUND_HALF_UP))
