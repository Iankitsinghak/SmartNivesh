"""Data source and evidence validation utilities."""


def validate_source(source) -> list[str]:
    """Validate DataSource object has required fields."""
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
    """Validate Evidence object has required fields."""
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
