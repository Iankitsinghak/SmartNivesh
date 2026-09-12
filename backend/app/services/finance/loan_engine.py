from app.core.constants import (
    MICRO_FINANCE_MAX_COST,
    MICRO_FINANCE_INTEREST,
    MICRO_FINANCE_TENURE_MONTHS,
    MICRO_FINANCE_MORATORIUM,
    MICRO_FINANCE_MAX_LOAN,
    TERM_LOAN_MAX_COST,
    TERM_LOAN_INTEREST,
    TERM_LOAN_TENURE_MONTHS,
    TERM_LOAN_MORATORIUM,
    TERM_LOAN_MAX_LOAN,
)
from app.core.enums import FinancingBand
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.schemas.finance import CostAssumptions, RevenueAssumptions, WorkingCapitalAssumptions

MONEY = Decimal("0.01")


def decimal_value(value: object) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)

def derive_project_cost(margin_capital: float) -> float:
    """
    Project Cost = Available Margin Capital / 10%
    """
    return float(money(decimal_value(margin_capital) / Decimal("0.10")))

def derive_loan_requirement(project_cost: float) -> float:
    """
    Loan Requirement = Project Cost * 90%
    """
    return float(money(decimal_value(project_cost) * Decimal("0.90")))


def derive_financing_structure(margin_capital: object, margin_percentage: object) -> tuple[Decimal, Decimal, Decimal]:
    margin = decimal_value(margin_capital)
    percentage = decimal_value(margin_percentage)
    if margin <= 0 or percentage <= 0 or percentage > 1:
        raise ValueError("Margin and margin percentage must be positive; percentage cannot exceed 1.")
    project_cost = money(margin / percentage)
    loan_amount = money(project_cost - margin)
    if money(margin + loan_amount) != project_cost:
        raise ValueError("Margin and loan amount do not reconcile to project cost.")
    return project_cost, money(margin), loan_amount


def calculate_revenue(assumptions: Optional[RevenueAssumptions]) -> tuple[Optional[Decimal], Optional[Decimal], str]:
    if assumptions is not None and assumptions.monthly_revenue is not None:
        return money(assumptions.monthly_revenue), None, "Monthly revenue is a direct user-supplied assumption."
    if assumptions is None or assumptions.selling_price is None:
        return None, None, "Selling price and sales volume are required; no revenue was assumed."
    if assumptions.units_sold is not None:
        units = assumptions.units_sold
        method = "Monthly revenue = monthly units sold × selling price."
    elif assumptions.daily_units is not None and assumptions.operating_days is not None:
        units = assumptions.daily_units * assumptions.operating_days
        method = "Monthly revenue = daily units × operating days × selling price."
    else:
        return None, None, "Selling price and either monthly units or daily units with operating days are required."
    return money(units * assumptions.selling_price), units, method


def calculate_costs(
    revenue: Optional[Decimal], monthly_units: Optional[Decimal], assumptions: Optional[CostAssumptions]
) -> tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal], Optional[Decimal], list[str]]:
    if assumptions is None:
        return None, None, None, None, ["Cost assumptions were not supplied."]
    fixed_values = [assumptions.rent, assumptions.salaries, assumptions.utilities, assumptions.maintenance,
                    assumptions.insurance, assumptions.other_fixed_costs]
    fixed_cost = money(assumptions.monthly_fixed_cost) if assumptions.monthly_fixed_cost is not None else money(sum((value or Decimal(0) for value in fixed_values), Decimal(0)))
    methods = ["Fixed cost is the direct monthly input." if assumptions.monthly_fixed_cost is not None else "Fixed costs are the sum of the user-supplied recurring cost fields."]
    variable_cost: Optional[Decimal] = None
    if assumptions.monthly_variable_cost is not None:
        variable_cost = money(assumptions.monthly_variable_cost)
        methods.append("Variable cost is the direct user-supplied monthly amount.")
    elif assumptions.variable_cost_ratio is not None and revenue is not None:
        variable_cost = money(revenue * assumptions.variable_cost_ratio)
        methods.append("Variable cost = monthly revenue × user-supplied variable-cost ratio.")
    elif assumptions.variable_cost_per_unit is not None and monthly_units is not None:
        variable_cost = money(monthly_units * assumptions.variable_cost_per_unit)
        methods.append("Variable cost = monthly units × user-supplied variable cost per unit.")
    else:
        methods.append("Variable cost is unknown because a compatible variable-cost input was not supplied.")
    if variable_cost is None:
        return None, fixed_cost, None, None, methods
    total = money(variable_cost + fixed_cost)
    profit = money(revenue - total) if revenue is not None else None
    return variable_cost, fixed_cost, total, profit, methods


def calculate_working_capital(
    assumptions: Optional[WorkingCapitalAssumptions], monthly_operating_cost: Optional[Decimal]
) -> tuple[Optional[Decimal], str]:
    if assumptions is None:
        return None, "Working-capital inputs were not supplied."
    explicit = any(value is not None for value in (
        assumptions.initial_inventory, assumptions.operating_cash_requirement,
        assumptions.receivables, assumptions.supplier_credit,
    ))
    if not explicit and assumptions.operating_buffer_months is None:
        return None, "At least one working-capital component or an operating buffer is required."
    buffer = Decimal(0)
    if assumptions.operating_buffer_months is not None:
        if monthly_operating_cost is None:
            return None, "Monthly operating cost is required to calculate the operating buffer."
        buffer = monthly_operating_cost * assumptions.operating_buffer_months
    requirement = (
        (assumptions.initial_inventory or Decimal(0))
        + (assumptions.operating_cash_requirement or Decimal(0))
        + (assumptions.receivables or Decimal(0))
        + buffer
        - (assumptions.supplier_credit or Decimal(0))
    )
    requirement = max(Decimal(0), requirement)
    return money(requirement), (
        "Working capital = inventory + operating cash + receivables + operating-cost buffer − supplier credit."
    )


def calculate_break_even(
    revenue_assumptions: Optional[RevenueAssumptions], cost_assumptions: Optional[CostAssumptions], fixed_cost: Optional[Decimal]
) -> tuple[Optional[Decimal], Optional[Decimal], str]:
    if not revenue_assumptions or revenue_assumptions.selling_price is None or fixed_cost is None:
        return None, None, "Selling price, fixed costs and variable cost per unit are required."
    if cost_assumptions is None or cost_assumptions.variable_cost_per_unit is None:
        return None, None, "Variable cost per unit is required for unit break-even calculation."
    contribution = revenue_assumptions.selling_price - cost_assumptions.variable_cost_per_unit
    if contribution <= 0:
        return money(contribution), None, "Break-even is impossible because contribution per unit is not positive."
    units = fixed_cost / contribution
    return money(contribution), units.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), (
        "Break-even units = monthly fixed costs ÷ contribution per unit."
    )

def determine_financing_band(project_cost: float) -> tuple[FinancingBand, dict]:
    """
    Returns the applicable financing band and its parameters based on project cost.
    """
    if project_cost <= MICRO_FINANCE_MAX_COST:
        return FinancingBand.MICRO_FINANCE, {
            "interest_rate": MICRO_FINANCE_INTEREST,
            "tenure_months": MICRO_FINANCE_TENURE_MONTHS,
            "moratorium_months": MICRO_FINANCE_MORATORIUM,
            "maximum_agency_loan": MICRO_FINANCE_MAX_LOAN
        }
    elif project_cost <= TERM_LOAN_MAX_COST:
        return FinancingBand.TERM_LOAN, {
            "interest_rate": TERM_LOAN_INTEREST,
            "tenure_months": TERM_LOAN_TENURE_MONTHS,
            "moratorium_months": TERM_LOAN_MORATORIUM,
            "maximum_agency_loan": TERM_LOAN_MAX_LOAN
        }
    else:
        return FinancingBand.UNSUPPORTED, {}
