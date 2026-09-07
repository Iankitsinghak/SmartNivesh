from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from app.core.enums import Confidence, Provenance


@dataclass(frozen=True)
class DataSource:
    source_id: str
    provider_name: str
    dataset_name: str
    source_url: str
    access_method: str
    publication_date: date
    geographic_coverage: str
    limitations: tuple[str, ...] = ()
    update_frequency: Optional[str] = None
    last_verified: Optional[date] = None


@dataclass(frozen=True)
class Evidence:
    indicator: str
    value: Any
    unit: str
    geographic_scope: str
    source: DataSource
    dataset_date: date
    provenance: Provenance
    method: Optional[str] = None
    formula: Optional[str] = None
    input_indicators: tuple[str, ...] = ()
    normalization: Optional[str] = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class Location:
    village: str
    district: str
    state: str
    latitude: float
    longitude: float


@dataclass
class SufficiencyResult:
    sufficient: bool
    missing_data: list[str] = field(default_factory=list)
    available_evidence: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    additional_data_required: list[str] = field(default_factory=list)
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.utils.provenance import DataClassification, ConfidenceLevel

class DataProvenance(BaseModel):
    source_id: str
    source_name: str
    source_url: Optional[str] = None
    data_type: DataClassification
    last_verified: Optional[datetime] = None
    confidence: ConfidenceLevel
    notes: Optional[str] = None

class DataQuality(BaseModel):
    confidence: ConfidenceLevel
    data_completeness: float = Field(ge=0.0, le=1.0)
    source_count: int
    verified_components: int
    estimated_components: int
