from app.schemas.market import Opportunity


def opportunity_report(opportunity: Opportunity) -> str:
    evidence = "\n".join(
        f"- {item.indicator}: {item.value} {item.unit}; {item.source.dataset_name}; "
        f"dataset date {item.dataset_date.isoformat()}; scope {item.geographic_scope}"
        for item in opportunity.evidence
    )
    limitations = "\n".join(f"- {item}" for item in opportunity.limitations)
    methodology = "\n".join(f"- {item}" for item in opportunity.methodology)
    return (
        f"# Potential Opportunity\n\n## {opportunity.title}\n\n"
        f"**Type:** {opportunity.opportunity_type.value}\n\n"
        f"**Evidence confidence:** {opportunity.data_confidence.value}\n\n"
        f"## Evidence\n{evidence}\n\n## Methodology\n{methodology}\n\n"
        f"## Limitations\n{limitations}\n\n"
        "Customer demand, willingness to pay, revenue, and market size were not inferred."
    )