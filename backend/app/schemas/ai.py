from dataclasses import dataclass


@dataclass(frozen=True)
class ExplanationResponse:
    text: str
    generated_by: str
    validated: bool