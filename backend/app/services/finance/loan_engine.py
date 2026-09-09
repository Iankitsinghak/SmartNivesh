def calculate_project_cost(available_margin: float, margin_percentage: float = 0.10) -> float:
    """
    Project Cost = Available Margin / 0.10
    """
    if available_margin < 0:
        raise ValueError("Available margin cannot be negative")
    if available_margin == 0:
        return 0.0
    if margin_percentage <= 0 or margin_percentage > 1:
        raise ValueError("Invalid margin percentage")
        
    return round(available_margin / margin_percentage, 2)

def calculate_loan_amount(project_cost: float, margin_percentage: float = 0.10) -> float:
    """
    Calculates the loan portion given a project cost and margin percentage.
    """
    if project_cost < 0:
        raise ValueError("Project cost cannot be negative")
        
    margin = project_cost * margin_percentage
    loan_amount = project_cost - margin
    return round(loan_amount, 2)
