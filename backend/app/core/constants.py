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

# --- Finance Engine Constants ---
MICRO_FINANCE_MAX_COST = 140000.0
MICRO_FINANCE_INTEREST = 6.5
MICRO_FINANCE_TENURE_MONTHS = 36
MICRO_FINANCE_MORATORIUM = 3
MICRO_FINANCE_MAX_LOAN = 125000.0

TERM_LOAN_MAX_COST = 5000000.0
TERM_LOAN_INTEREST = 8.0
TERM_LOAN_TENURE_MONTHS = 84
TERM_LOAN_MORATORIUM = 6
TERM_LOAN_MAX_LOAN = 4500000.0

# --- Scheme Configuration ---
SCHEME_CONFIG_MICRO_FINANCE = {
    "scheme_code": "MF-01",
    "name": "Micro Finance Scheme",
    "financing_percentage": 90.0,
    "maximum_loan": MICRO_FINANCE_MAX_LOAN,
    "interest_rate": MICRO_FINANCE_INTEREST,
    "tenure_years": MICRO_FINANCE_TENURE_MONTHS // 12,
    "moratorium_months": MICRO_FINANCE_MORATORIUM,
    "max_project_cost": MICRO_FINANCE_MAX_COST
}

SCHEME_CONFIG_TERM_LOAN = {
    "scheme_code": "TL-01",
    "name": "Term Loan Scheme",
    "financing_percentage": 90.0,
    "maximum_loan": TERM_LOAN_MAX_LOAN,
    "interest_rate": TERM_LOAN_INTEREST,
    "tenure_years": TERM_LOAN_TENURE_MONTHS // 12,
    "moratorium_months": TERM_LOAN_MORATORIUM,
    "max_project_cost": TERM_LOAN_MAX_COST
}
