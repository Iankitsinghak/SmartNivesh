from decimal import Decimal, ROUND_HALF_UP
from typing import List
from app.schemas.finance import RepaymentScheduleRow

def generate_amortization_schedule(principal: float, annual_interest_rate: float, tenure_months: int, monthly_emi: float) -> List[RepaymentScheduleRow]:
    """
    Generates a deterministic amortization schedule.
    Assumes standard EMI payments. 
    Does not factor moratorium deferred interest logic unless specified.
    """
    schedule = []
    
    principal_value = Decimal(str(principal))
    rate_value = Decimal(str(annual_interest_rate))
    emi_value = Decimal(str(monthly_emi))
    cent = Decimal("0.01")
    if principal_value < 0 or rate_value < 0 or emi_value < 0:
        raise ValueError("Principal, rate and EMI cannot be negative.")
    if tenure_months <= 0:
        raise ValueError("Tenure must be greater than zero.")
    if principal_value == 0:
        return schedule
        
    r = rate_value / Decimal(12) / Decimal(100)
    current_balance = principal_value
    
    for i in range(1, tenure_months + 1):
        interest_payment = (current_balance * r).quantize(cent, rounding=ROUND_HALF_UP)
        
        # In the final month, adjust the payment so balance goes exactly to 0
        if i == tenure_months:
            payment = (current_balance + interest_payment).quantize(cent, rounding=ROUND_HALF_UP)
            principal_payment = current_balance
            closing_balance = Decimal(0)
        else:
            payment = emi_value
            principal_payment = (payment - interest_payment).quantize(cent, rounding=ROUND_HALF_UP)
            closing_balance = (current_balance - principal_payment).quantize(cent, rounding=ROUND_HALF_UP)
            if closing_balance < 0:
                principal_payment = current_balance
                payment = (principal_payment + interest_payment).quantize(cent, rounding=ROUND_HALF_UP)
                closing_balance = Decimal(0)
            
        schedule.append(RepaymentScheduleRow(
            installment_number=i,
            opening_balance=float(current_balance),
            interest_component=float(interest_payment),
            principal_component=float(principal_payment),
            payment=float(payment),
            closing_balance=float(closing_balance)
        ))
        
        current_balance = closing_balance
        
    return schedule
