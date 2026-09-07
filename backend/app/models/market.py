from dataclasses import dataclass

from app.core.enums import Provenance


@dataclass(frozen=True)
class ActivityRecord:
    indicator: str
    value: float
    unit: str
    geographic_scope: str
    source_id: str
    dataset_date: str
    provenance: Provenance