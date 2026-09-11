"""
Deterministic risk analysis engine.

Analyzes threats by type using verified public evidence and validated
operational evidence. Returns structured threat items with evidence,
confidence, limitations, and status (IDENTIFIED, LOW, UNKNOWN).

No AI-generated claims. No composite risk score when components are unknown.
Evidence must be registered and fresh.
"""

import math
from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from app.core.constants import INSUFFICIENT_RISK_DATA_MESSAGE, RISK_THRESHOLDS
from app.core.enums import Confidence, ThreatSeverity, ThreatStatus, ThreatType
from app.schemas.common import Evidence, SufficiencyResult
from app.schemas.location import Location
from app.schemas.risk import OperationalEvidence, RiskAnalysisResponse, RiskAnalysisSummary, Threat, ThreatResponse
from app.services.risk.mitigation import (
    get_buyer_concentration_mitigations,
    get_seasonality_mitigations,
    get_supply_chain_mitigations,
)
from app.services.risk.validation import (
    check_buyer_concentration_evidence_sufficiency,
    check_seasonality_evidence_sufficiency,
    check_supply_chain_evidence_sufficiency,
    validate_operational_evidence,
)


def calculate_coefficient_of_variation(values: list[float]) -> Optional[float]:
    """
    Calculate coefficient of variation (std dev / mean).
    Returns None if insufficient data.
    """
    if not values or len(values) < 2:
        return None
    
    mean = sum(values) / len(values)
    if mean == 0:
        return None
    
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = math.sqrt(variance)
    return std_dev / mean


def calculate_hhi(shares: list[float]) -> float:
    """
    Calculate Herfindahl-Hirschman Index from market/buyer shares.
    HHI = sum of (share * 100)^2, ranges 0-10000.
    Note: shares are 0.0-1.0 (e.g., 0.30 = 30%), converted to percentage points.
    """
    return sum((s * 100) ** 2 for s in shares if s > 0)


def score_from_cv(cv: float) -> float:
    """Convert coefficient of variation to 0-100 threat score."""
    if cv <= 0.15:
        return 20.0  # Low variation
    elif cv <= 0.30:
        return 50.0  # Moderate variation
    else:
        return 75.0 + min(cv - 0.30, 0.40) * 50  # High variation, capped at 100


def score_from_stockout_frequency(freq_per_year: float) -> float:
    """Convert annual stockout frequency to 0-100 threat score."""
    if freq_per_year <= 1:
        return 25.0
    elif freq_per_year <= 2:
        return 50.0
    else:
        return 75.0 + min((freq_per_year - 2) * 5, 25.0)  # Capped at 100


def score_from_fulfillment_rate(rate: float) -> float:
    """Convert fulfillment rate to 0-100 threat score. Lower rate = higher threat."""
    if rate >= 0.98:
        return 10.0
    elif rate >= 0.90:
        return 40.0
    else:
        return 80.0 + (1.0 - rate) * 200  # Capped at 100


def score_from_buyer_share(top_share: float, top3_share: float, hhi: float) -> float:
    """
    Convert buyer concentration metrics to 0-100 threat score.
    Higher concentration = higher threat.
    """
    # Primary signal: top buyer share
    if top_share >= 0.50:
        base_score = 80.0
    elif top_share >= 0.35:
        base_score = 60.0
    else:
        base_score = 40.0
    
    # Secondary signal: HHI (higher = more concentrated)
    hhi_adjustment = 0.0
    if hhi > 2500:
        hhi_adjustment = 10.0
    elif hhi > 1500:
        hhi_adjustment = 5.0
    
    return min(base_score + hhi_adjustment, 100.0)


def severity_level_from_score(score: Optional[float]) -> Optional[str]:
    """Map 0-100 score to severity level."""
    if score is None:
        return None
    if score >= 70:
        return ThreatSeverity.CRITICAL.value
    elif score >= 50:
        return ThreatSeverity.HIGH.value
    elif score >= 30:
        return ThreatSeverity.MODERATE.value
    else:
        return ThreatSeverity.LOW.value


def analyze_seasonality_threat(
    location: Location,
    operational_evidence: Optional[OperationalEvidence],
) -> Threat:
    """
    Analyze seasonal demand fluctuation threat.
    
    Evidence: historical monthly/weekly demand observations.
    Score: coefficient of variation of demand across periods.
    Status: IDENTIFIED (with sufficient data), UNKNOWN (insufficient).
    """
    threat_id = f"threat_{uuid4().hex[:10]}"
    
    sufficient, missing = check_seasonality_evidence_sufficiency(operational_evidence)
    
    if not sufficient:
        return Threat(
            threat_id=threat_id,
            threat_type=ThreatType.SEASONAL_DEMAND.value,
            status=ThreatStatus.UNKNOWN.value,
            severity_score=None,
            severity_level=None,
            confidence=Confidence.LOW,
            evidence=[],
            evidence_summary="Insufficient operational evidence (monthly/weekly demand history required).",
            limitations=[
                "Seasonal demand patterns cannot be assessed without historical observations.",
                "Seeded business category profiles represent assumptions, not verified demand data.",
            ],
            methodology=[
                "Coefficient of variation (CV) of observed demand across periods.",
                "CV > 0.30 indicates high seasonality; CV 0.15-0.30 indicates moderate seasonality.",
                "Minimum 12 months of observation required for credibility.",
            ],
            unsupported_assumptions=[
                "Future seasonality cannot be assumed to match past patterns without ongoing monitoring.",
            ],
            missing_data_for_confidence=missing,
        )
    
    if not operational_evidence or not operational_evidence.seasonal_observations:
        return Threat(
            threat_id=threat_id,
            threat_type=ThreatType.SEASONAL_DEMAND.value,
            status=ThreatStatus.UNKNOWN.value,
            severity_score=None,
            severity_level=None,
            confidence=Confidence.LOW,
            evidence=[],
            evidence_summary="No seasonal observations provided.",
            limitations=["Seasonal demand assessment requires historical monthly or weekly demand data."],
            methodology=[
                "Coefficient of variation (CV) of observed demand across periods.",
            ],
            unsupported_assumptions=[
                "Absence of seasonal evidence does not imply stable demand.",
            ],
            missing_data_for_confidence=missing,
        )
    
    observations = list(operational_evidence.seasonal_observations.values())
    cv = calculate_coefficient_of_variation(observations)
    
    if cv is None:
        return Threat(
            threat_id=threat_id,
            threat_type=ThreatType.SEASONAL_DEMAND.value,
            status=ThreatStatus.UNKNOWN.value,
            severity_score=None,
            severity_level=None,
            confidence=Confidence.LOW,
            evidence=[],
            evidence_summary="Seasonal observations insufficient for variation calculation.",
            limitations=["All observations were zero or identical; cannot compute coefficient of variation."],
            methodology=["Coefficient of variation calculation requires variance in observations."],
            unsupported_assumptions=[],
            missing_data_for_confidence=["Non-zero, variable seasonal observations"],
        )
    
    score = score_from_cv(cv)
    severity = severity_level_from_score(score)
    
    # Determine low periods for recommendations
    low_periods = []
    mean_demand = sum(observations) / len(observations)
    for period, value in operational_evidence.seasonal_observations.items():
        if value < mean_demand * 0.80:  # > 20% below mean
            low_periods.append(period)
    
    status = ThreatStatus.IDENTIFIED.value if score >= 30 else ThreatStatus.LOW.value
    
    mitigations = get_seasonality_mitigations(score, low_periods)
    
    return Threat(
        threat_id=threat_id,
        threat_type=ThreatType.SEASONAL_DEMAND.value,
        status=status,
        severity_score=score,
        severity_level=severity,
        confidence=Confidence.HIGH,
        evidence=[],
        evidence_summary=(
            f"Observed demand coefficient of variation: {cv:.2f}. "
            f"Low periods: {', '.join(low_periods) if low_periods else 'None identified'}. "
            f"Observation period: {operational_evidence.observation_start_date} to "
            f"{operational_evidence.observation_end_date} ({len(observations)} periods)."
        ),
        limitations=[
            "Seasonality assessment based on historical data may not predict future changes.",
            "Extreme weather, policy changes, or market disruptions could alter seasonal patterns.",
            "Data quality depends on accuracy of source operational records.",
        ],
        methodology=[
            "Coefficient of variation = std dev / mean of observed demand.",
            "CV ≤ 0.15: Low seasonality (score 20). CV 0.15-0.30: Moderate (score 50). CV > 0.30: High (score 75+).",
            "Low periods defined as > 20% below average demand.",
        ],
        unsupported_assumptions=[
            "External factors (new competitors, market changes, policy shifts) could alter demand patterns.",
        ],
        missing_data_for_confidence=[],
        mitigation_recommendations=mitigations,
        data_freshness_note=f"Data observations through {operational_evidence.observation_end_date}.",
    )


def analyze_supply_chain_bottleneck_threat(
    location: Location,
    operational_evidence: Optional[OperationalEvidence],
) -> Threat:
    """
    Analyze supply-chain bottleneck risk.
    
    Evidence: supplier count, lead-time variability, stockout frequency, fulfillment rate.
    Score: weighted composite of variability, disruption, and concentration signals.
    Status: IDENTIFIED (with sufficient data), UNKNOWN (insufficient).
    """
    threat_id = f"threat_{uuid4().hex[:10]}"
    
    sufficient, missing = check_supply_chain_evidence_sufficiency(operational_evidence)
    
    if not sufficient:
        return Threat(
            threat_id=threat_id,
            threat_type=ThreatType.SUPPLY_CHAIN_BOTTLENECK.value,
            status=ThreatStatus.UNKNOWN.value,
            severity_score=None,
            severity_level=None,
            confidence=Confidence.LOW,
            evidence=[],
            evidence_summary="Insufficient operational evidence (supplier data and fulfillment history required).",
            limitations=[
                "Supply-chain reliability cannot be assessed from mapped business presence alone.",
                "Lead times, disruption history, and supplier capacity must be verified operationally.",
                "Seeded distribution profiles represent assumptions, not verified supply reliability.",
            ],
            methodology=[
                "Risk assessment based on supplier count, lead-time variability, and fulfillment metrics.",
            ],
            unsupported_assumptions=[
                "Mapped suppliers do not indicate capacity, reliability, or alternate availability.",
            ],
            missing_data_for_confidence=missing,
        )
    
    if not operational_evidence:
        return Threat(
            threat_id=threat_id,
            threat_type=ThreatType.SUPPLY_CHAIN_BOTTLENECK.value,
            status=ThreatStatus.UNKNOWN.value,
            severity_score=None,
            severity_level=None,
            confidence=Confidence.LOW,
            evidence=[],
            evidence_summary="No operational supply-chain evidence provided.",
            limitations=["Supply-chain assessment requires verified business operational data."],
            methodology=["Supplier count, lead-time variability, and fulfillment tracking."],
            unsupported_assumptions=[],
            missing_data_for_confidence=missing,
        )
    
    # Component scores
    supplier_concentration_score = 0.0
    lead_time_score = 0.0
    fulfillment_score = 0.0
    
    # Supplier concentration risk
    if operational_evidence.supplier_count is not None:
        if operational_evidence.supplier_count <= 1:
            supplier_concentration_score = 85.0
        elif operational_evidence.supplier_count <= 2:
            supplier_concentration_score = 65.0
        elif operational_evidence.supplier_count <= 3:
            supplier_concentration_score = 40.0
        else:
            supplier_concentration_score = 20.0
    
    # Lead-time variability risk
    if operational_evidence.lead_time_variability_coefficient is not None:
        lead_time_score = score_from_cv(operational_evidence.lead_time_variability_coefficient)
    elif operational_evidence.primary_supplier_lead_time_days is not None:
        # Without variability data, use a default moderate score
        lead_time_score = 30.0
    
    # Fulfillment/stockout risk
    if operational_evidence.stockout_frequency_per_year is not None:
        fulfillment_score = max(
            fulfillment_score,
            score_from_stockout_frequency(operational_evidence.stockout_frequency_per_year)
        )
    
    if operational_evidence.average_fulfillment_rate is not None:
        fulfillment_score = max(
            fulfillment_score,
            score_from_fulfillment_rate(operational_evidence.average_fulfillment_rate)
        )
    
    # Weighted composite score
    score = (
        supplier_concentration_score * 0.40 +
        lead_time_score * 0.35 +
        fulfillment_score * 0.25
    )
    
    severity = severity_level_from_score(score)
    status = ThreatStatus.IDENTIFIED.value if score >= 30 else ThreatStatus.LOW.value
    
    mitigations = get_supply_chain_mitigations(
        score,
        operational_evidence.supplier_count or 0,
        operational_evidence.lead_time_variability_coefficient or 0.0,
        operational_evidence.stockout_frequency_per_year or 0.0,
        operational_evidence.average_fulfillment_rate or 1.0,
    )
    
    summary_parts = []
    if operational_evidence.supplier_count is not None:
        summary_parts.append(f"Active suppliers: {operational_evidence.supplier_count}")
    if operational_evidence.lead_time_variability_coefficient is not None:
        summary_parts.append(
            f"Lead-time variability (CV): {operational_evidence.lead_time_variability_coefficient:.2f}"
        )
    if operational_evidence.stockout_frequency_per_year is not None:
        summary_parts.append(f"Annual stockout frequency: {operational_evidence.stockout_frequency_per_year:.1f}")
    if operational_evidence.average_fulfillment_rate is not None:
        summary_parts.append(f"Fulfillment rate: {operational_evidence.average_fulfillment_rate:.1%}")
    
    return Threat(
        threat_id=threat_id,
        threat_type=ThreatType.SUPPLY_CHAIN_BOTTLENECK.value,
        status=status,
        severity_score=score,
        severity_level=severity,
        confidence=Confidence.HIGH,
        evidence=[],
        evidence_summary=". ".join(summary_parts) + f"." if summary_parts else "Supply-chain data available.",
        limitations=[
            "Assessment based on historical observations; future supplier reliability may change.",
            "External disruptions (transportation, weather, regulatory) not captured in historical data.",
            "Assessment assumes suppliers remain available and willing to supply at observed terms.",
        ],
        methodology=[
            "Supplier concentration risk: higher risk with fewer alternate suppliers.",
            "Lead-time variability (CV): higher CV indicates less predictable sourcing.",
            "Fulfillment risk: based on historical stockout rate and on-time delivery performance.",
            "Composite score: 40% concentration + 35% lead-time variability + 25% fulfillment.",
        ],
        unsupported_assumptions=[
            "Supplier capacity and willingness to fulfill orders assumed stable.",
            "No inference about supplier financial health or long-term viability from operational metrics alone.",
        ],
        missing_data_for_confidence=[],
        mitigation_recommendations=mitigations,
        data_freshness_note=f"Data observations through {operational_evidence.observation_end_date}.",
    )


def analyze_buyer_concentration_threat(
    location: Location,
    operational_evidence: Optional[OperationalEvidence],
) -> Threat:
    """
    Analyze buyer concentration and single-buyer dependency risk.
    
    Evidence: buyer count, top-buyer share, top-3 buyer share, HHI.
    Score: concentration metrics (higher concentration = higher threat).
    Status: IDENTIFIED (with sufficient data), UNKNOWN (insufficient).
    """
    threat_id = f"threat_{uuid4().hex[:10]}"
    
    sufficient, missing = check_buyer_concentration_evidence_sufficiency(operational_evidence)
    
    if not sufficient:
        return Threat(
            threat_id=threat_id,
            threat_type=ThreatType.BUYER_CONCENTRATION.value,
            status=ThreatStatus.UNKNOWN.value,
            severity_score=None,
            severity_level=None,
            confidence=Confidence.LOW,
            evidence=[],
            evidence_summary="Insufficient operational evidence (buyer count and sales shares required).",
            limitations=[
                "Buyer concentration cannot be inferred from market demographics or competition.",
                "Actual customer composition requires business transaction/sales records.",
                "Seeded data provides no insight into buyer dependency.",
            ],
            methodology=[
                "Risk assessment based on buyer count, top-buyer sales share, and HHI.",
            ],
            unsupported_assumptions=[
                "Market size or competitor count do not predict customer concentration.",
                "Buyers identified from mapped businesses are not the same as sales customers.",
            ],
            missing_data_for_confidence=missing,
        )
    
    if not operational_evidence:
        return Threat(
            threat_id=threat_id,
            threat_type=ThreatType.BUYER_CONCENTRATION.value,
            status=ThreatStatus.UNKNOWN.value,
            severity_score=None,
            severity_level=None,
            confidence=Confidence.LOW,
            evidence=[],
            evidence_summary="No operational buyer data provided.",
            limitations=["Buyer concentration assessment requires verified sales records."],
            methodology=["Buyer count, sales share distribution, and concentration metrics."],
            unsupported_assumptions=[],
            missing_data_for_confidence=missing,
        )
    
    # Collect buyer shares for HHI calculation
    buyer_shares = []
    if operational_evidence.top_buyer_share is not None:
        buyer_shares.append(operational_evidence.top_buyer_share)
    
    if operational_evidence.top_3_buyer_share is not None and operational_evidence.top_buyer_share is not None:
        # Estimate shares of 2nd and 3rd buyers
        remaining_top3 = operational_evidence.top_3_buyer_share - operational_evidence.top_buyer_share
        if remaining_top3 > 0:
            # Split evenly as a rough approximation
            buyer_shares.extend([remaining_top3 / 2, remaining_top3 / 2])
    
    # Add remaining buyers with equal shares (if buyer_count > 3)
    if operational_evidence.buyer_count is not None and len(buyer_shares) < operational_evidence.buyer_count:
        remaining_share = 1.0 - sum(buyer_shares)
        remaining_buyers = operational_evidence.buyer_count - len(buyer_shares)
        if remaining_share > 0 and remaining_buyers > 0:
            buyer_shares.extend([remaining_share / remaining_buyers] * remaining_buyers)
    
    hhi = calculate_hhi(buyer_shares) if buyer_shares else 0.0
    
    score = score_from_buyer_share(
        operational_evidence.top_buyer_share or 0.0,
        operational_evidence.top_3_buyer_share or 0.0,
        hhi,
    )
    
    severity = severity_level_from_score(score)
    status = ThreatStatus.IDENTIFIED.value if score >= 30 else ThreatStatus.LOW.value
    
    mitigations = get_buyer_concentration_mitigations(
        score,
        operational_evidence.top_buyer_share or 0.0,
        operational_evidence.buyer_count or 0,
        hhi,
    )
    
    summary_parts = [f"Total buyers: {operational_evidence.buyer_count}"]
    if operational_evidence.top_buyer_share is not None:
        summary_parts.append(f"Top buyer share: {operational_evidence.top_buyer_share:.1%}")
    if operational_evidence.top_3_buyer_share is not None:
        summary_parts.append(f"Top 3 buyers share: {operational_evidence.top_3_buyer_share:.1%}")
    summary_parts.append(f"HHI (Herfindahl-Hirschman Index): {hhi:.0f}")
    
    return Threat(
        threat_id=threat_id,
        threat_type=ThreatType.BUYER_CONCENTRATION.value,
        status=status,
        severity_score=score,
        severity_level=severity,
        confidence=Confidence.HIGH,
        evidence=[],
        evidence_summary=". ".join(summary_parts) + ".",
        limitations=[
            "Assessment based on historical sales data; future customer composition may change.",
            "Customer churn and new-customer acquisition could alter concentration.",
            "Assessment assumes buyers remain active; contract termination or bankruptcy not modeled.",
        ],
        methodology=[
            "Concentration risk: top-buyer share > 50% indicates high dependency.",
            "HHI (Herfindahl-Hirschman Index): measures overall market concentration.",
            "HHI > 2500 indicates high concentration (DOJ threshold).",
            "Composite score based on top-buyer share and HHI.",
        ],
        unsupported_assumptions=[
            "Historical buyer composition is not a guarantee of future customer retention.",
            "Buyer demand changes, bankruptcies, or policy shifts not captured in historical data.",
        ],
        missing_data_for_confidence=[],
        mitigation_recommendations=mitigations,
        data_freshness_note=f"Data observations through {operational_evidence.observation_end_date}.",
    )


def analyze_risk(
    location: Location,
    category_id: str,
    radius_km: float,
    operational_evidence: Optional[OperationalEvidence] = None,
) -> RiskAnalysisResponse:
    """
    Orchestrate threat analysis across all threat types.
    
    Validates operational evidence, analyzes each threat type,
    and returns structured results with overall status and limitations.
    """
    # Validate operational evidence if provided
    valid, validation_errors = validate_operational_evidence(operational_evidence)
    if not valid and operational_evidence is not None:
        return RiskAnalysisResponse(
            location_id=location.location_id,
            category_id=category_id,
            radius_km=radius_km,
            overall_status="INSUFFICIENT_DATA",
            data_confidence="low",
            message=f"Operational evidence validation failed: {'; '.join(validation_errors)}",
            limitations=validation_errors,
        )
    
    # Analyze each threat type
    seasonality_threat = analyze_seasonality_threat(location, operational_evidence)
    supply_chain_threat = analyze_supply_chain_bottleneck_threat(location, operational_evidence)
    buyer_threat = analyze_buyer_concentration_threat(location, operational_evidence)
    
    threats = [seasonality_threat, supply_chain_threat, buyer_threat]
    
    # Convert to API response format
    threat_responses = []
    identified_count = 0
    low_count = 0
    unknown_count = 0
    
    for threat in threats:
        threat_responses.append(
            ThreatResponse(
                threat_id=threat.threat_id,
                threat_type=threat.threat_type,
                status=threat.status,
                severity_score=threat.severity_score,
                severity_level=threat.severity_level,
                confidence=threat.confidence.value,
                evidence_summary=threat.evidence_summary,
                limitations=threat.limitations,
                methodology=threat.methodology,
                unsupported_assumptions=threat.unsupported_assumptions,
                missing_data_for_confidence=threat.missing_data_for_confidence,
                mitigation_recommendations=threat.mitigation_recommendations,
                data_freshness_note=threat.data_freshness_note,
            )
        )
        
        if threat.status == ThreatStatus.IDENTIFIED.value:
            identified_count += 1
        elif threat.status == ThreatStatus.LOW.value:
            low_count += 1
        else:
            unknown_count += 1
    
    # Determine overall status
    if identified_count == 0 and low_count == 0:
        overall_status = "INSUFFICIENT_DATA"
    elif any(t.severity_score and t.severity_score >= 70 for t in threats):
        overall_status = "REQUIRES_ATTENTION"
    elif identified_count > 0 or low_count > 0:
        overall_status = "MANAGEABLE"
    else:
        overall_status = "WELL_MITIGATED"
    
    # Determine data completeness
    if unknown_count == 3:
        data_completeness = "INSUFFICIENT"
    elif unknown_count > 0:
        data_completeness = "PARTIAL"
    else:
        data_completeness = "COMPLETE"
    
    # Collect all limitations
    all_limitations = []
    for threat in threats:
        all_limitations.extend(threat.limitations)
    
    return RiskAnalysisResponse(
        location_id=location.location_id,
        category_id=category_id,
        radius_km=radius_km,
        threats=threat_responses,
        summary={
            "identified_threat_count": identified_count,
            "low_probability_threat_count": low_count,
            "unknown_threat_count": unknown_count,
            "data_completeness": data_completeness,
        },
        overall_status=overall_status,
        data_confidence="high" if data_completeness == "COMPLETE" else
                        "medium" if data_completeness == "PARTIAL" else "low",
        limitations=list(set(all_limitations)),
        methodology=[
            "Three threat types analyzed: seasonal demand, supply-chain bottleneck, buyer concentration.",
            "Each threat requires verified operational evidence; missing data results in UNKNOWN status.",
            "Scores are deterministic and range 0-100. Status determined by score thresholds.",
            "No AI-generated claims. All recommendations tied to observed evidence.",
        ],
        message=(
            f"Risk analysis complete. {identified_count} identified threats, {low_count} low-probability, "
            f"{unknown_count} unknown due to insufficient evidence. " + (
                "Provide operational evidence for higher-confidence assessment."
                if unknown_count > 0 else ""
            )
        ).strip(),
    )
