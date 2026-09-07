from collections.abc import Iterable
from uuid import uuid4

from app.core.constants import INSUFFICIENT_EVIDENCE_MESSAGE
from app.core.enums import EvidenceSufficiency, OpportunityType
from app.schemas.common import Evidence, Location
from app.schemas.market import Opportunity, OpportunityAnalysis
from app.services.opportunity.scoring import (
    confidence_for,
    identified_provider_count,
    qualitative_supply_gap,
)
from app.services.opportunity.validation import check_evidence_sufficiency


REQUIRED_INDICATORS: dict[OpportunityType, tuple[str, ...]] = {
    OpportunityType.GEOGRAPHIC_SERVICE_GAP: (
        "identified_providers",
        "nearest_identified_provider",
    ),
    OpportunityType.LOCAL_SUPPLY_GAP: ("identified_providers", "local_activity"),
    OpportunityType.INFRASTRUCTURE_GAP: ("identified_facilities", "population_or_coverage"),
    OpportunityType.AGRICULTURE_LINKED: ("agricultural_activity", "identified_providers"),
    OpportunityType.LIVESTOCK_LINKED: ("livestock_activity", "identified_providers"),
    OpportunityType.RESOURCE_LINKED: ("local_resource", "identified_providers"),
}


def analyze_opportunity(
    *,
    location: Location,
    title: str,
    opportunity_type: OpportunityType,
    evidence: Iterable[Evidence],
) -> OpportunityAnalysis:
    evidence_list = list(evidence)
    sufficiency = check_evidence_sufficiency(
        evidence_list, REQUIRED_INDICATORS[opportunity_type]
    )
    if not sufficiency.sufficient:
        return OpportunityAnalysis(sufficiency=sufficiency, message=INSUFFICIENT_EVIDENCE_MESSAGE)

    provider_count = next(
        (int(item.value) for item in evidence_list if item.indicator == "identified_providers"),
        None,
    )
    limitations = [*sufficiency.limitations]
    if provider_count is not None:
        limitations.insert(
            0,
            "No provider was identified in the available dataset; this does not prove that no provider exists."
            if provider_count == 0
            else "Provider counts represent identified records, not a complete business census.",
        )
    opportunity = Opportunity(
        opportunity_id=f"opp_{uuid4().hex[:10]}",
        title=title,
        opportunity_type=opportunity_type,
        location=location,
        evidence=evidence_list,
        data_confidence=confidence_for(evidence_list),
        limitations=limitations,
        methodology=[
            "Evaluate only the required indicators for this opportunity type.",
            "Retain source, dataset date, geographic scope, and limitations for each indicator.",
        ],
        unsupported_assumptions=[
            "Customer demand, willingness to pay, revenue, and market size were not inferred."
        ],
        supply_gap=qualitative_supply_gap(provider_count) if provider_count is not None else "moderate",
        accessibility_gap="moderate",
        local_need_evidence="moderate",
        data_coverage="high" if all(item.source.source_id for item in evidence_list) else "moderate",
    )
    return OpportunityAnalysis(
        sufficiency=sufficiency,
        opportunity=opportunity,
        status=EvidenceSufficiency.SUFFICIENT,
    )


def analyze_geographic_service_gap(
    *, location: Location, title: str, evidence: Iterable[Evidence]
) -> OpportunityAnalysis:
    return analyze_opportunity(
        location=location,
        title=title,
        opportunity_type=OpportunityType.GEOGRAPHIC_SERVICE_GAP,
        evidence=evidence,
    )