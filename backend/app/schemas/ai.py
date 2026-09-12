from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class ExplanationResponse:
    text: str
    generated_by: str
    validated: bool


class AssistantRequest(BaseModel):
    """A bounded, assessment-grounded question for the user-facing assistant."""

    question: str = Field(min_length=2, max_length=1000)
    language: Literal["en", "hi"] = "en"
    assessment_context: dict[str, Any] = Field(default_factory=dict)


class AssistantResponse(BaseModel):
    answer: str
    language: Literal["en", "hi"]
    generated_by: Literal["gemini", "safe_fallback"]
    limitations: list[str] = Field(default_factory=list)
