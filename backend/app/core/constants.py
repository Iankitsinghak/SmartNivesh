INSUFFICIENT_EVIDENCE_MESSAGE = (
    "Insufficient evidence to identify a reliable opportunity from the available public data."
)

RADIUS_BANDS_KM = ((0.0, 2.0), (2.0, 5.0), (5.0, 10.0))
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

# Risk/Threat analysis thresholds
RISK_THRESHOLDS = {
    "SEASONALITY": {
        "coefficient_variation_high": 0.30,  # CV > 0.30 = high seasonal variation
        "coefficient_variation_moderate": 0.15,  # CV 0.15-0.30 = moderate
        "min_observation_periods": 12,  # Minimum months of data for credibility
    },
    "SUPPLY_CHAIN": {
        "lead_time_cv_high": 0.35,  # High variability in lead times
        "lead_time_cv_moderate": 0.20,
        "stockout_frequency_high_per_year": 4,  # 4+ stockouts/year = high risk
        "stockout_frequency_moderate_per_year": 2,
        "supplier_concentration_threshold": 3,  # < 3 suppliers = high concentration
        "fulfillment_rate_low": 0.90,  # < 90% fulfillment = moderate risk
        "min_observation_periods": 6,  # Minimum months of operational data
    },
    "BUYER_CONCENTRATION": {
        "top_buyer_share_high": 0.50,  # > 50% from one buyer = high risk
        "top_buyer_share_moderate": 0.35,
        "top_3_buyer_share_high": 0.75,  # > 75% from top 3 = high risk
        "hhi_high": 2500,  # HHI > 2500 = high concentration (DOJ threshold)
        "hhi_moderate": 1500,
        "min_buyer_count": 5,  # Minimum distinct buyers for credibility
        "min_observation_periods": 6,  # Minimum months of sales data
    },
}

INSUFFICIENT_RISK_DATA_MESSAGE = (
    "Insufficient operational data to assess this threat. "
    "Verified business-owned evidence (sales records, supplier data, historical observations) "
    "is required for accurate risk quantification."
)
