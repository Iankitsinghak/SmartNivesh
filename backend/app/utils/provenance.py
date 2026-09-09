# Removed top level import of app.schemas.common

def validate_source(source) -> list[str]:
    from app.schemas.common import DataSource
    missing: list[str] = []
    required = {
        "source_id": source.source_id,
        "provider_name": source.provider_name,
        "dataset_name": source.dataset_name,
        "source_url": source.source_url,
        "access_method": source.access_method,
        "geographic_coverage": source.geographic_coverage,
    }
    missing.extend(name for name, value in required.items() if not value)
    if source.publication_date is None:
        missing.append("publication_date")
    return missing


def validate_evidence(evidence) -> list[str]:
    from app.schemas.common import Evidence
    missing = validate_source(evidence.source)
    if evidence.value is None:
        missing.append("value")
    if not evidence.unit:
        missing.append("unit")
    if not evidence.geographic_scope:
        missing.append("geographic_scope")
    if evidence.dataset_date is None:
        missing.append("dataset_date")
    return missing
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
