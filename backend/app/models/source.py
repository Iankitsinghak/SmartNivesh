from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    provider_name: str
    dataset_name: str
    source_url: str
    access_method: str
    publication_date: date
    geographic_coverage: str
    limitations: tuple[str, ...]
    update_frequency: str | None = None
    last_verified: date | None = None