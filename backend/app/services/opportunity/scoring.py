from collections.abc import Iterable

from app.core.enums import Confidence
from app.schemas.common import Evidence


def identified_provider_count(evidence: Iterable[Evidence]) -> int:
    for item in evidence:
        if item.indicator == "identified_providers":
            return int(item.value)
    raise ValueError("identified_providers evidence is required")


def qualitative_supply_gap(provider_count: int) -> str:
    if provider_count == 0:
        return "high"
    if provider_count <= 2:
        return "moderate"
    return "low"


def confidence_for(evidence: Iterable[Evidence]) -> Confidence:
    values = {item.source.source_id for item in evidence}
    if not values:
        return Confidence.LOW
    if all(item.provenance.value == "verified" for item in evidence):
        return Confidence.HIGH
    return Confidence.MEDIUM