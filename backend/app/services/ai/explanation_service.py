from app.services.ai.fallback import build_fallback_explanation
from app.services.ai.validator import validate_explanation
from app.schemas.market import Opportunity
from app.schemas.ai import ExplanationResponse


def explain(opportunity: Opportunity, generated_text: str | None = None) -> str:
    if generated_text:
        errors = validate_explanation(generated_text, opportunity)
        if not errors:
            return generated_text
    return build_fallback_explanation(opportunity)


def explain_response(
    opportunity: Opportunity, generated_text: str | None = None
) -> ExplanationResponse:
    if generated_text and not validate_explanation(generated_text, opportunity):
        return ExplanationResponse(generated_text, "llm", True)
    return ExplanationResponse(build_fallback_explanation(opportunity), "template", True)