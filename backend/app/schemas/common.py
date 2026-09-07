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
