from app.schemas.finance import RevenueAssumptions, CostAssumptions, ScenarioResult, ValueWithStatus
from app.core.enums import DataStatus
from app.services.finance.repayment import calculate_repayment_coverage

def calculate_scenario(
    scenario_type: str,
    revenue_assumptions: RevenueAssumptions,
    cost_assumptions: CostAssumptions,
    emi: float,
    revenue_multiplier: float = 1.0,
    variable_cost_multiplier: float = 1.0,
    fixed_cost_multiplier: float = 1.0
) -> ScenarioResult:
    """
    Calculates revenue, costs, and profit for a given scenario.
    """
    revenue_val = None
    revenue_status = DataStatus.UNKNOWN
    
    if revenue_assumptions.units_per_month is not None and revenue_assumptions.selling_price is not None:
        revenue_val = revenue_assumptions.units_per_month * revenue_assumptions.selling_price * revenue_multiplier
        revenue_status = DataStatus.CALCULATED
        
    variable_cost_val = None
    variable_cost_status = DataStatus.UNKNOWN
    
    if revenue_val is not None and cost_assumptions.variable_cost_ratio is not None:
        variable_cost_val = revenue_val * cost_assumptions.variable_cost_ratio * variable_cost_multiplier
        variable_cost_status = DataStatus.CALCULATED
        
    fixed_cost_val = None
    fixed_cost_status = DataStatus.UNKNOWN
    
    if cost_assumptions.fixed_costs_per_month is not None:
        fixed_cost_val = cost_assumptions.fixed_costs_per_month * fixed_cost_multiplier
        fixed_cost_status = DataStatus.CALCULATED
        
    profit_val = None
    profit_status = DataStatus.UNKNOWN
    
    if revenue_val is not None and variable_cost_val is not None and fixed_cost_val is not None:
        profit_val = revenue_val - variable_cost_val - fixed_cost_val
        profit_status = DataStatus.CALCULATED
        
    coverage_val = calculate_repayment_coverage(profit_val, emi) if profit_val is not None else None
    coverage_status = DataStatus.CALCULATED if coverage_val is not None else DataStatus.UNKNOWN
    
    return ScenarioResult(
        scenario_type=scenario_type,
        revenue=ValueWithStatus(value=round(revenue_val, 2) if revenue_val is not None else None, status=revenue_status),
        variable_cost=ValueWithStatus(value=round(variable_cost_val, 2) if variable_cost_val is not None else None, status=variable_cost_status),
        fixed_cost=ValueWithStatus(value=round(fixed_cost_val, 2) if fixed_cost_val is not None else None, status=fixed_cost_status),
        operating_profit=ValueWithStatus(value=round(profit_val, 2) if profit_val is not None else None, status=profit_status),
        repayment_coverage=ValueWithStatus(value=coverage_val, status=coverage_status)
    )

def generate_all_scenarios(revenue_assumptions: RevenueAssumptions, cost_assumptions: CostAssumptions, emi: float):
    """
    Generates BASE, CONSERVATIVE, and OPTIMISTIC scenarios.
    """
    base = calculate_scenario("BASE", revenue_assumptions, cost_assumptions, emi)
    conservative = calculate_scenario("CONSERVATIVE", revenue_assumptions, cost_assumptions, emi, revenue_multiplier=0.8, variable_cost_multiplier=1.1, fixed_cost_multiplier=1.1)
    optimistic = calculate_scenario("OPTIMISTIC", revenue_assumptions, cost_assumptions, emi, revenue_multiplier=1.2, variable_cost_multiplier=0.9, fixed_cost_multiplier=1.0)
    
    return base, conservative, optimistic
