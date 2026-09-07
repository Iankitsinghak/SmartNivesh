MARKET_GAP_WEIGHTS = {
    "demand": 0.45,
    "demand_growth": 0.25,
    "distribution_availability": 0.20,
    "competition": -0.10
}

OPPORTUNITY_SCORE_WEIGHTS = {
    "market_demand": 0.25,
    "opportunity_gap": 0.15,
    "capital_fit": 0.20,
    "skill_fit": 0.15,
    "asset_fit": 0.10,
    "distribution_fit": 0.10,
    "risk_adjustment": 0.05
}

SCORE_THRESHOLDS = {
    "WEAK": (0, 39),
    "MODERATE": (40, 59),
    "GOOD": (60, 74),
    "STRONG": (75, 89),
    "VERY_STRONG": (90, 100)
}
