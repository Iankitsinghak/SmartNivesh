from app.schemas.finance import FinancialAnalysisRequest, FinancialAnalysisResponse, FinancialFeasibilityIndicators, ValueWithStatus
from app.core.enums import DataStatus
from app.services.finance.loan_engine import calculate_project_cost, calculate_loan_amount
from app.services.finance.repayment import calculate_repayment
from app.services.finance.scenarios import generate_all_scenarios
from app.services.finance.recommended_financing import calculate_recommended_financing

def analyze_finance(request: FinancialAnalysisRequest) -> FinancialAnalysisResponse:
    # 1. Loan Engine
    project_cost = calculate_project_cost(request.available_margin, 0.10)
    margin = request.available_margin
    loan_amount = calculate_loan_amount(project_cost, 0.10)
    
    # 2. EMI & Repayment
    repayment_data = calculate_repayment(loan_amount, request.loan_assumptions.annual_interest_rate, request.loan_assumptions.tenure_months)
    monthly_emi = repayment_data["monthly_emi"]
    
    # 3. Scenarios
    base_scen, cons_scen, opt_scen = generate_all_scenarios(request.revenue_assumptions, request.cost_assumptions, monthly_emi)
    
    # 4. Break-even
    break_even_val = None
    break_even_status = DataStatus.UNKNOWN
    
    if (request.revenue_assumptions.selling_price is not None and 
        request.cost_assumptions.variable_cost_ratio is not None and 
        request.cost_assumptions.fixed_costs_per_month is not None):
        
        vc_per_unit = request.revenue_assumptions.selling_price * request.cost_assumptions.variable_cost_ratio
        contribution_margin = request.revenue_assumptions.selling_price - vc_per_unit
        
        if contribution_margin > 0:
            break_even_val = round(request.cost_assumptions.fixed_costs_per_month / contribution_margin, 2)
            break_even_status = DataStatus.CALCULATED
            
    # Working capital
    working_capital_val = None
    working_capital_status = DataStatus.UNKNOWN
    if request.cost_assumptions.initial_inventory is not None and request.cost_assumptions.operating_buffer_months is not None:
        fixed_costs = request.cost_assumptions.fixed_costs_per_month or 0.0
        working_capital_val = round(request.cost_assumptions.initial_inventory + (request.cost_assumptions.operating_buffer_months * fixed_costs), 2)
        working_capital_status = DataStatus.ESTIMATED
    
    # 5. Recommendation
    base_profit = base_scen.operating_profit.value
    cons_profit = cons_scen.operating_profit.value
    
    recommendation = calculate_recommended_financing(
        project_cost=project_cost,
        margin_percentage=0.10,
        base_profit=base_profit,
        conservative_profit=cons_profit,
        monthly_emi=monthly_emi,
        loan_amount=loan_amount
    )
    
    financial_score_val = 100.0 if recommendation.financial_feasibility == "FEASIBLE" else 50.0
    
    indicators = FinancialFeasibilityIndicators(
        financial_score=ValueWithStatus(value=financial_score_val, status=DataStatus.CALCULATED),
        break_even_units=ValueWithStatus(value=break_even_val, status=break_even_status),
        working_capital_requirement=ValueWithStatus(value=working_capital_val, status=working_capital_status)
    )
    
    return FinancialAnalysisResponse(
        project_cost=ValueWithStatus(value=project_cost, status=DataStatus.CALCULATED),
        margin_contribution=ValueWithStatus(value=margin, status=DataStatus.CALCULATED),
        loan_amount=ValueWithStatus(value=loan_amount, status=DataStatus.CALCULATED),
        monthly_emi=ValueWithStatus(value=monthly_emi, status=DataStatus.CALCULATED),
        total_repayment=ValueWithStatus(value=repayment_data["total_repayment"], status=DataStatus.CALCULATED),
        total_interest=ValueWithStatus(value=repayment_data["total_interest"], status=DataStatus.CALCULATED),
        base_scenario=base_scen,
        conservative_scenario=cons_scen,
        optimistic_scenario=opt_scen,
        recommended_financing=recommendation,
        feasibility_indicators=indicators
    )
