import json

from dataclasses import asdict

from app.schemas.market import Opportunity


def build_explanation_prompt(opportunity: Opportunity) -> str:
    payload = asdict(opportunity)
    payload["opportunity_type"] = opportunity.opportunity_type.value
    payload["data_confidence"] = opportunity.data_confidence.value
    return (
        "Explain only the supplied evidence. Do not infer demand, revenue, prices, market size, "
        "willingness to pay, trends, or real-world absence. State limitations clearly.\n\n"
        + json.dumps(payload, default=str, ensure_ascii=True)
    )