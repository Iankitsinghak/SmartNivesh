from dataclasses import dataclass

from app.core.enums import OpportunityType
from app.schemas.common import Evidence, Location
from app.schemas.market import OpportunityAnalysis
from app.services.opportunity.opportunity_engine import analyze_opportunity


@dataclass(frozen=True)
class OpportunityRequest:
    location: Location
    title: str
    opportunity_type: OpportunityType
    evidence: tuple[Evidence, ...]


def create_opportunity_analysis(request: OpportunityRequest) -> OpportunityAnalysis:
    return analyze_opportunity(
        location=request.location,
        title=request.title,
        opportunity_type=request.opportunity_type,
        evidence=request.evidence,
    )