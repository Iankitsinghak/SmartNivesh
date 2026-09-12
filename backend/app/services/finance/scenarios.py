from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.schemas.finance import ScenarioConfiguration, ScenarioResult


def _number(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def generate_all_scenarios(
    monthly_revenue: Optional[Decimal],
    monthly_operating_cost: Optional[Decimal],
    monthly_emi: Decimal,
    configuration: ScenarioConfiguration,
) -> list[ScenarioResult]:
    """Calculate explicit, deterministic downside/base/upside scenarios."""
    definitions = (
        ("CONSERVATIVE", configuration.conservative_revenue_multiplier, configuration.conservative_cost_multiplier),
        ("BASE", Decimal(1), Decimal(1)),
        ("OPTIMISTIC", configuration.optimistic_revenue_multiplier, configuration.optimistic_cost_multiplier),
    )
    results: list[ScenarioResult] = []
    for name, revenue_multiplier, cost_multiplier in definitions:
        if monthly_revenue is None or monthly_operating_cost is None:
            results.append(ScenarioResult(
                name=name, status="UNKNOWN", revenue_multiplier=float(revenue_multiplier),
                cost_multiplier=float(cost_multiplier),
            ))
            continue
        revenue = monthly_revenue * revenue_multiplier
        cost = monthly_operating_cost * cost_multiplier
        profit = revenue - cost
        coverage = None if monthly_emi <= 0 else profit / monthly_emi
        results.append(ScenarioResult(
            name=name,
            status="CALCULATED",
            revenue_multiplier=float(revenue_multiplier),
            cost_multiplier=float(cost_multiplier),
            monthly_revenue=_number(revenue),
            monthly_operating_cost=_number(cost),
            operating_profit=_number(profit),
            repayment_coverage=None if coverage is None else float(coverage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            monthly_cash_after_emi=_number(profit - monthly_emi),
        ))
    return results
