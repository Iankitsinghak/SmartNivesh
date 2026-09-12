"""Grounded natural-language explanations for an already computed assessment."""

import logging

from fastapi import APIRouter

from app.schemas.ai import AssistantRequest, AssistantResponse
from app.services.ai.assistant import AssistantUnavailable, _fallback, answer_assessment_question


router = APIRouter(prefix="/api/assistant", tags=["Assessment Assistant"])
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=AssistantResponse)
async def ask_assessment_assistant(request: AssistantRequest) -> AssistantResponse:
    try:
        return answer_assessment_question(request.question, request.language, request.assessment_context)
    except AssistantUnavailable as exc:
        logger.info("Assessment assistant unavailable: %s", exc)
        # A transient upstream AI outage must not make the assessment unusable.
        # The response explicitly labels this as a fallback rather than presenting
        # it as a generated or newly verified conclusion.
        return _fallback(request.language)
