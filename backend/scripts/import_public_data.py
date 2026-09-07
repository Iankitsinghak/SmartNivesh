from collections.abc import Iterable
from datetime import date

from app.core.enums import Provenance
from app.utils.normalization import normalize_indicator_name, parse_dataset_date


def normalize_public_record(
    record: dict[str, object], *, source_id: str, dataset_date: str
) -> dict[str, object]:
    """Validate the metadata required before a public record enters analysis."""
    if not source_id:
        raise ValueError("source_id is required")
    parsed_date = parse_dataset_date(dataset_date)
    if not record.get("geographic_scope"):
        raise ValueError("geographic_scope is required")
    if record.get("value") is None:
        raise ValueError("value is required")
    indicator = record.get("indicator")
    if not isinstance(indicator, str) or not indicator.strip():
        raise ValueError("indicator is required")
    return {
        "indicator": normalize_indicator_name(indicator),
        "value": record["value"],
        "unit": record.get("unit", "unspecified"),
        "geographic_scope": record["geographic_scope"],
        "source_id": source_id,
        "dataset_date": parsed_date,
        "provenance": Provenance.VERIFIED,
    }


def normalize_public_records(
    records: Iterable[dict[str, object]], *, source_id: str, dataset_date: str
) -> list[dict[str, object]]:
    return [
        normalize_public_record(record, source_id=source_id, dataset_date=dataset_date)
        for record in records
    ]