"""
Threat Identification schemas.

Structured threat analysis with evidence-backed scores, confidence, limitations,
and deterministic mitigation recommendations. Threats are typed (SEASONAL_DEMAND,
SUPPLY_CHAIN_BOTTLENECK, BUYER_CONCENTRATION) and include evidence, provenance,
methodology, unsupported assumptions, and status (IDENTIFIED, LOW, UNKNOWN).

No raw buyer PII. Private operational evidence is labeled distinctly from public
verified datasets.
"""

from dataclasses import dataclass, field
from typing import Optional

from app.core.enums import Confidence
from app.schemas.common import Evidence, Location, SufficiencyResult
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class OperationalEvidence:
    """
    Business-owned operational evidence for threat analysis.
    
    Private data: exclude raw buyer/supplier names, PII, contract terms.
    Include only anonymized/aggregated metrics over a defined observation period.
    """

    observation_period_days: int  # Minimum required observation window
    observation_start_date: str  # ISO 8601 date
    observation_end_date: str  # ISO 8601 date
    data_classification: str  # "BUSINESS_OWNED", "VERIFIED_THIRD_PARTY", etc.

    # Seasonality evidence: monthly or weekly demand observations
    seasonal_observations: dict[str, float] = field(default_factory=dict)  # {"January": 1000, "February": 800, ...}

    # Supply-chain evidence
    supplier_count: Optional[int] = None  # Total number of active suppliers
    alternate_supplier_count: Optional[int] = None  # Suppliers with capability to fill orders
    primary_supplier_lead_time_days: Optional[float] = None
    lead_time_variability_coefficient: Optional[float] = None  # Std dev / mean
    stockout_frequency_per_year: Optional[float] = None
    supply_disruption_events: Optional[int] = None  # Count of logistics/fulfillment failures
    average_fulfillment_rate: Optional[float] = None  # 0.0 to 1.0

    # Buyer-dependency evidence (anonymized/aggregated)
    buyer_count: Optional[int] = None  # Total distinct buyers
    top_buyer_share: Optional[float] = None  # Sales/value share of largest buyer, 0.0-1.0
    top_3_buyer_share: Optional[float] = None  # Cumulative share of top 3, 0.0-1.0
    buyer_concentration_hhi: Optional[float] = None  # Herfindahl-Hirschman Index, 0-10000
    contract_dependency_count: Optional[int] = None  # Buyers with formal contracts
    customer_churn_rate_annual: Optional[float] = None  # Fraction of buyers lost per year


@dataclass(frozen=True)
class Threat:
    """
    A structured threat item with type, severity, evidence, confidence, and mitigation.
    Status determines whether the threat is identified, low-probability, or unknown.
    """

    threat_id: str  # Unique identifier
    threat_type: str  # SEASONAL_DEMAND, SUPPLY_CHAIN_BOTTLENECK, BUYER_CONCENTRATION
    status: str  # IDENTIFIED, LOW, UNKNOWN (insufficient evidence)
    severity_score: Optional[float] = None  # 0-100 if status is IDENTIFIED or LOW; None if UNKNOWN
    severity_level: Optional[str] = None  # "CRITICAL", "HIGH", "MODERATE", "LOW"
    confidence: Confidence = Confidence.MEDIUM
    evidence: list[Evidence] = field(default_factory=list)
    evidence_summary: str = ""  # Human-readable summary of evidence basis

    limitations: list[str] = field(default_factory=list)
    methodology: list[str] = field(default_factory=list)
    unsupported_assumptions: list[str] = field(default_factory=list)
    missing_data_for_confidence: list[str] = field(default_factory=list)

    mitigation_recommendations: list[str] = field(default_factory=list)
    data_freshness_note: Optional[str] = None


@dataclass(frozen=True)
class RiskAnalysisSummary:
    """
    Compact threat summary for inclusion in MarketAnalysisResponse.
    Preserves backward compatibility while exposing structured results.
    """

    identified_threat_count: int
    low_probability_threat_count: int
    unknown_threat_count: int
    threats_requiring_attention: list[str]  # High/critical severity threat descriptions
    data_completeness: str  # "COMPLETE", "PARTIAL", "INSUFFICIENT"
    limitations: list[str]


class RiskAnalysisRequest(BaseModel):
    """Request to analyze threats at a location for a business category."""

    location_id: str
    category_id: str
    radius_km: float = 10.0
    operational_evidence: Optional[OperationalEvidence] = None


class ThreatResponse(BaseModel):
    """Structured threat item for API responses."""

    threat_id: str
    threat_type: str
    status: str
    severity_score: Optional[float] = Field(None, ge=0, le=100)
    severity_level: Optional[str] = None
    confidence: str = "medium"
    evidence_summary: str = ""
    limitations: list[str] = Field(default_factory=list)
    methodology: list[str] = Field(default_factory=list)
    unsupported_assumptions: list[str] = Field(default_factory=list)
    missing_data_for_confidence: list[str] = Field(default_factory=list)
    mitigation_recommendations: list[str] = Field(default_factory=list)
    data_freshness_note: Optional[str] = None


class RiskAnalysisResponse(BaseModel):
    """Complete risk analysis output."""

    location_id: str
    category_id: str
    radius_km: float
    threats: list[ThreatResponse] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)  # identified_count, low_count, unknown_count, completeness
    overall_status: str  # "WELL_MITIGATED", "MANAGEABLE", "REQUIRES_ATTENTION", "INSUFFICIENT_DATA"
    data_confidence: str = "medium"
    limitations: list[str] = Field(default_factory=list)
    methodology: list[str] = Field(default_factory=list)
    sufficiency: Optional[dict] = None  # SufficiencyResult serialized
    message: Optional[str] = None
