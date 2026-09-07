from app.schemas.market import Opportunity


FORBIDDEN_CLAIMS = (
    "willing to pay",
    "customers want",
    "people need",
    "guaranteed revenue",
    "market size",
    "no provider exists",
)


def validate_explanation(text: str, opportunity: Opportunity) -> list[str]:
    lowered = text.lower()
    errors = [f"unsupported claim: {claim}" for claim in FORBIDDEN_CLAIMS if claim in lowered]
    for item in opportunity.evidence:
        if str(item.value).lower() not in lowered:
            errors.append(f"untraceable evidence value: {item.value}")
    if "limitation" not in lowered and "limit" not in lowered:
        errors.append("missing limitations")
    return errors