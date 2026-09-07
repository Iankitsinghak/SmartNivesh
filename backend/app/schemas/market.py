from dataclasses import dataclass, field
from typing import Optional

from app.core.enums import Confidence, EvidenceSufficiency, OpportunityType
from app.schemas.common import Evidence, Location, SufficiencyResult


@dataclass
class Opportunity:
    opportunity_id: str
    title: str
    opportunity_type: OpportunityType
    location: Location
    evidence: list[Evidence]
    data_confidence: Confidence
    limitations: list[str]
    methodology: list[str]
    unsupported_assumptions: list[str] = field(default_factory=list)
    supply_gap: Optional[str] = None
    accessibility_gap: Optional[str] = None
    local_need_evidence: Optional[str] = None
    data_coverage: Optional[str] = None


@dataclass
class OpportunityAnalysis:
    sufficiency: SufficiencyResult
    opportunity: Optional[Opportunity] = None
    message: Optional[str] = None
    status: EvidenceSufficiency = EvidenceSufficiency.INSUFFICIENT