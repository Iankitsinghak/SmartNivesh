from collections.abc import Iterable

from app.schemas.common import Evidence, SufficiencyResult
from app.utils.provenance import validate_evidence


def check_evidence_sufficiency(
    evidence: Iterable[Evidence], required_indicators: Iterable[str]
) -> SufficiencyResult:
    evidence_list = list(evidence)
    by_indicator = {item.indicator: item for item in evidence_list}
    missing_data: list[str] = []
    available = sorted(by_indicator)
    limitations: list[str] = []
    additional: list[str] = []

    for indicator in required_indicators:
        item = by_indicator.get(indicator)
        if item is None:
            missing_data.append(indicator)
            additional.append(f"A publicly verifiable {indicator} dataset")
            continue
        invalid_fields = validate_evidence(item)
        if invalid_fields:
            missing_data.extend(f"{indicator}.{field}" for field in invalid_fields)
        limitations.extend(item.limitations)
        limitations.extend(item.source.limitations)

    return SufficiencyResult(
        sufficient=not missing_data,
        missing_data=sorted(set(missing_data)),
        available_evidence=available,
        limitations=sorted(set(limitations)),
        additional_data_required=sorted(set(additional)),
    )