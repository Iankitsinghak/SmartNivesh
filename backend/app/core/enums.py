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