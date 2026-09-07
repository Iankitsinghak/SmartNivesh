from app.schemas.market import Opportunity


def build_fallback_explanation(opportunity: Opportunity) -> str:
    evidence_lines = [
        f"- {item.indicator}: {item.value} {item.unit} ({item.geographic_scope}; "
        f"{item.source.dataset_name}, {item.dataset_date.isoformat()})"
        for item in opportunity.evidence
    ]
    limitations = "\n".join(f"- {item}" for item in opportunity.limitations)
    evidence = "\n".join(evidence_lines)
    return (
        f"### Potential Opportunity\n{opportunity.title}\n\n"
        "**Why identified**\n"
        "The available public dataset indicates a measurable local supply or accessibility gap.\n\n"
        f"**Evidence confidence:** {opportunity.data_confidence.value}\n\n"
        f"**Evidence**\n{evidence}\n\n"
        f"**Important limitations**\n{limitations}"
    )