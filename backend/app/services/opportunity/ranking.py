from app.schemas.market import Opportunity


def rank_key(opportunity: Opportunity) -> tuple[int, int, int]:
    levels = {"low": 0, "moderate": 1, "high": 2}
    return (
        levels.get(opportunity.supply_gap or "low", 0),
        levels.get(opportunity.accessibility_gap or "low", 0),
        levels.get(opportunity.data_coverage or "low", 0),
    )


def rank_opportunities(opportunities: list[Opportunity]) -> list[Opportunity]:
    return sorted(opportunities, key=rank_key, reverse=True)