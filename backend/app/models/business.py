from dataclasses import dataclass

from app.core.enums import Provenance


@dataclass(frozen=True)
class BusinessRecord:
    business_id: str
    category: str
    name: str
    latitude: float
    longitude: float
    source_id: str
    dataset_date: str
    provenance: Provenance