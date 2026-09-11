"""
Risk evidence validation.

Validates operational evidence completeness, data freshness, and consistency.
Extends common provenance validation for risk-specific requirements.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from app.core.constants import RISK_THRESHOLDS
from app.schemas.risk import OperationalEvidence


def validate_operational_evidence(evidence: Optional[OperationalEvidence]) -> tuple[bool, list[str]]:
    """
    Validate operational evidence structure and data quality.
    
    Returns (is_valid, error_messages).
    """
    if evidence is None:
        return True, []  # No operational evidence is not an error; analysis will use UNKNOWN
    
    errors: list[str] = []

    # Parse dates
    try:
        start = datetime.fromisoformat(evidence.observation_start_date).date()
        end = datetime.fromisoformat(evidence.observation_end_date).date()
    except (ValueError, TypeError) as e:
        errors.append(f"Invalid date format: {e}")
        return False, errors

    # Validate observation window
    if end < start:
        errors.append("Observation end date must be after start date")
    
    window_days = (end - start).days
    if window_days < 1:
        errors.append("Observation window must span at least 1 day")
    
    if window_days < evidence.observation_period_days:
        errors.append(
            f"Observation window ({window_days} days) is shorter than declared requirement "
            f"({evidence.observation_period_days} days)"
        )

    # Check data freshness (should not be more than 2 years old)
    if (date.today() - end).days > 730:
        errors.append(
            f"Operational evidence is stale (ended {(date.today() - end).days} days ago). "
            "Recent data is required for reliable risk assessment."
        )

    # Validate seasonal observations
    if evidence.seasonal_observations:
        for period, value in evidence.seasonal_observations.items():
            if not isinstance(value, (int, float)):
                errors.append(f"Seasonal observation '{period}' must be numeric, got {type(value)}")
            elif value < 0:
                errors.append(f"Seasonal observation '{period}' must be non-negative")

    # Validate numeric fields: non-negative where required
    if evidence.supplier_count is not None and evidence.supplier_count < 0:
        errors.append("supplier_count must be non-negative")
    
    if evidence.alternate_supplier_count is not None:
        if evidence.alternate_supplier_count < 0:
            errors.append("alternate_supplier_count must be non-negative")
        if evidence.supplier_count is not None and evidence.alternate_supplier_count > evidence.supplier_count:
            errors.append("alternate_supplier_count cannot exceed supplier_count")

    if evidence.primary_supplier_lead_time_days is not None and evidence.primary_supplier_lead_time_days < 0:
        errors.append("primary_supplier_lead_time_days must be non-negative")

    if evidence.lead_time_variability_coefficient is not None:
        if evidence.lead_time_variability_coefficient < 0:
            errors.append("lead_time_variability_coefficient must be non-negative")

    if evidence.stockout_frequency_per_year is not None and evidence.stockout_frequency_per_year < 0:
        errors.append("stockout_frequency_per_year must be non-negative")

    if evidence.supply_disruption_events is not None and evidence.supply_disruption_events < 0:
        errors.append("supply_disruption_events must be non-negative")

    # Validate percentages (0.0-1.0)
    if evidence.average_fulfillment_rate is not None:
        if not (0.0 <= evidence.average_fulfillment_rate <= 1.0):
            errors.append(f"average_fulfillment_rate must be 0.0-1.0, got {evidence.average_fulfillment_rate}")

    if evidence.top_buyer_share is not None:
        if not (0.0 <= evidence.top_buyer_share <= 1.0):
            errors.append(f"top_buyer_share must be 0.0-1.0, got {evidence.top_buyer_share}")

    if evidence.top_3_buyer_share is not None:
        if not (0.0 <= evidence.top_3_buyer_share <= 1.0):
            errors.append(f"top_3_buyer_share must be 0.0-1.0, got {evidence.top_3_buyer_share}")
        if evidence.top_buyer_share is not None and evidence.top_3_buyer_share < evidence.top_buyer_share:
            errors.append("top_3_buyer_share must be >= top_buyer_share")

    if evidence.buyer_count is not None and evidence.buyer_count < 0:
        errors.append("buyer_count must be non-negative")

    if evidence.contract_dependency_count is not None:
        if evidence.contract_dependency_count < 0:
            errors.append("contract_dependency_count must be non-negative")
        if evidence.buyer_count is not None and evidence.contract_dependency_count > evidence.buyer_count:
            errors.append("contract_dependency_count cannot exceed buyer_count")

    if evidence.customer_churn_rate_annual is not None:
        if not (0.0 <= evidence.customer_churn_rate_annual <= 1.0):
            errors.append(f"customer_churn_rate_annual must be 0.0-1.0, got {evidence.customer_churn_rate_annual}")

    return len(errors) == 0, errors


def check_seasonality_evidence_sufficiency(evidence: Optional[OperationalEvidence]) -> tuple[bool, list[str]]:
    """
    Check if seasonal evidence is sufficient for seasonality threat analysis.
    Returns (sufficient, missing_items).
    """
    if evidence is None:
        return False, ["Seasonal observations required (monthly or weekly historical data)"]
    
    missing = []
    
    if not evidence.seasonal_observations:
        missing.append("seasonal_observations (dictionary of period:value)")
    elif len(evidence.seasonal_observations) < RISK_THRESHOLDS["SEASONALITY"]["min_observation_periods"]:
        missing.append(
            f"seasonal_observations must have at least "
            f"{RISK_THRESHOLDS['SEASONALITY']['min_observation_periods']} periods, "
            f"got {len(evidence.seasonal_observations)}"
        )
    
    return len(missing) == 0, missing


def check_supply_chain_evidence_sufficiency(evidence: Optional[OperationalEvidence]) -> tuple[bool, list[str]]:
    """
    Check if supply-chain evidence is sufficient for bottleneck analysis.
    Returns (sufficient, missing_items).
    """
    if evidence is None:
        return False, [
            "supplier_count (total active suppliers)",
            "lead_time_variability or primary_supplier_lead_time_days",
            "stockout_frequency_per_year or supply_disruption_events",
        ]
    
    missing = []
    
    if evidence.supplier_count is None:
        missing.append("supplier_count (total active suppliers)")
    
    if evidence.primary_supplier_lead_time_days is None and evidence.lead_time_variability_coefficient is None:
        missing.append("lead_time_variability_coefficient or primary_supplier_lead_time_days")
    
    if evidence.stockout_frequency_per_year is None and evidence.supply_disruption_events is None:
        missing.append("stockout_frequency_per_year or supply_disruption_events")
    
    return len(missing) == 0, missing


def check_buyer_concentration_evidence_sufficiency(evidence: Optional[OperationalEvidence]) -> tuple[bool, list[str]]:
    """
    Check if buyer evidence is sufficient for concentration threat analysis.
    Returns (sufficient, missing_items).
    """
    if evidence is None:
        return False, [
            "buyer_count (distinct buyers)",
            "top_buyer_share (sales/value share of largest buyer, 0.0-1.0)",
        ]
    
    missing = []
    
    if evidence.buyer_count is None:
        missing.append("buyer_count (distinct buyers)")
    elif evidence.buyer_count < RISK_THRESHOLDS["BUYER_CONCENTRATION"]["min_buyer_count"]:
        missing.append(
            f"buyer_count must be at least "
            f"{RISK_THRESHOLDS['BUYER_CONCENTRATION']['min_buyer_count']}, "
            f"got {evidence.buyer_count}"
        )
    
    if evidence.top_buyer_share is None:
        missing.append("top_buyer_share (sales/value share of largest buyer, 0.0-1.0)")
    
    return len(missing) == 0, missing
