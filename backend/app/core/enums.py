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


class DataStatus(str, Enum):
    CALCULATED = "CALCULATED"
    ESTIMATED = "ESTIMATED"
    ASSUMPTION = "ASSUMPTION"
    UNKNOWN = "UNKNOWN"

class FinancialStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    LOAN_CAP_EXCEEDED = "LOAN_CAP_EXCEEDED"
    PROJECT_RANGE_EXCEEDED = "PROJECT_RANGE_EXCEEDED"
    INVALID_INPUT = "INVALID_INPUT"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"

class FinancingBand(str, Enum):
    MICRO_FINANCE = "MICRO_FINANCE"
    TERM_LOAN = "TERM_LOAN"
    UNSUPPORTED = "UNSUPPORTED"

class DataClassification(str, Enum):
    ASSUMPTION = "ASSUMPTION"
    CALCULATED = "CALCULATED"
    VERIFIED = "VERIFIED"

class EligibilityStatus(str, Enum):
    PENDING = "PENDING"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"