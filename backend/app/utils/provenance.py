from enum import Enum

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
