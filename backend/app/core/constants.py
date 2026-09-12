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

# Deterministic baseline finance parameters.  Scheme routing reads these same
# values, preventing the legacy /analyze endpoint and /schemes/route from
# drifting apart.
MICRO_FINANCE_MAX_COST = 140_000
MICRO_FINANCE_INTEREST = 6.5
MICRO_FINANCE_TENURE_MONTHS = 36
MICRO_FINANCE_MORATORIUM = 3
MICRO_FINANCE_MAX_LOAN = 125_000
TERM_LOAN_MAX_COST = 5_000_000
TERM_LOAN_INTEREST = 8.0
TERM_LOAN_TENURE_MONTHS = 84
TERM_LOAN_MORATORIUM = 6
TERM_LOAN_MAX_LOAN = 4_500_000

SCHEME_CONFIG_MICRO_FINANCE = {
    "scheme_code": "MF-01", "name": "NSFDC Micro Finance Scheme",
    "max_project_cost": MICRO_FINANCE_MAX_COST, "maximum_loan": MICRO_FINANCE_MAX_LOAN,
    "interest_rate": MICRO_FINANCE_INTEREST, "tenure_years": 3,
    "moratorium_months": MICRO_FINANCE_MORATORIUM, "financing_percentage": 0.90,
}
SCHEME_CONFIG_TERM_LOAN = {
    "scheme_code": "TL-01", "name": "NSFDC Term Loan",
    "max_project_cost": TERM_LOAN_MAX_COST, "maximum_loan": TERM_LOAN_MAX_LOAN,
    "interest_rate": TERM_LOAN_INTEREST, "tenure_years": 7,
    "moratorium_months": TERM_LOAN_MORATORIUM, "financing_percentage": 0.90,
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
