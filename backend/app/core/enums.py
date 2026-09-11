from enum import Enum


class OpportunityType(str, Enum):
    GEOGRAPHIC_SERVICE_GAP = "geographic_service_gap"
    LOCAL_SUPPLY_GAP = "local_supply_gap"
    INFRASTRUCTURE_GAP = "infrastructure_gap"
    AGRICULTURE_LINKED = "agriculture_linked"
    LIVESTOCK_LINKED = "livestock_linked"
    RESOURCE_LINKED = "resource_linked"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Provenance(str, Enum):
    VERIFIED = "verified"
    CALCULATED = "calculated"
    ESTIMATED = "estimated"
    SEEDED_DEMO = "seeded_demo"
    ASSUMPTION = "assumption"
    AI_INTERPRETATION = "ai_interpretation"


class EvidenceSufficiency(str, Enum):
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"


class ThreatType(str, Enum):
    SEASONAL_DEMAND = "seasonal_demand"
    SUPPLY_CHAIN_BOTTLENECK = "supply_chain_bottleneck"
    BUYER_CONCENTRATION = "buyer_concentration"


class ThreatStatus(str, Enum):
    IDENTIFIED = "identified"
    LOW = "low"
    UNKNOWN = "unknown"


class ThreatSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class DataClassification(str, Enum):
    VERIFIED = "VERIFIED"
    CALCULATED = "CALCULATED"
    ESTIMATED = "ESTIMATED"
    SEEDED_DEMO = "SEEDED_DEMO"
    ASSUMPTION = "ASSUMPTION"
    AI_INTERPRETATION = "AI_INTERPRETATION"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class DemandLevel(str, Enum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"
    UNKNOWN = "UNKNOWN"