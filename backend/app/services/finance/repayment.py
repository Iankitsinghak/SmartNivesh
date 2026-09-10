from typing import List, Dict, Any
from app.schemas.finance import RepaymentScheduleRow

def generate_amortization_schedule(principal: float, annual_interest_rate: float, tenure_months: int, monthly_emi: float) -> List[RepaymentScheduleRow]:
    """
    Generates a deterministic amortization schedule.
    Assumes standard EMI payments. 
    Does not factor moratorium deferred interest logic unless specified.
    """
    schedule = []
    
    if principal <= 0 or tenure_months <= 0:
        return schedule
        
    r = (annual_interest_rate / 12.0) / 100.0
    current_balance = principal
    
    for i in range(1, tenure_months + 1):
        interest_payment = round(current_balance * r, 2)
        
        # In the final month, adjust the payment so balance goes exactly to 0
        if i == tenure_months:
            payment = current_balance + interest_payment
            principal_payment = current_balance
            closing_balance = 0.0
        else:
            payment = monthly_emi
            principal_payment = round(payment - interest_payment, 2)
            closing_balance = round(current_balance - principal_payment, 2)
            
        schedule.append(RepaymentScheduleRow(
            installment_number=i,
            opening_balance=current_balance,
            interest_component=interest_payment,
            principal_component=principal_payment,
            payment=payment,
            closing_balance=closing_balance
        ))
        
        current_balance = closing_balance
        
    return schedule
