"""Grounded Gemini explanations for VyaparSathi assessment results.

The assistant does not calculate finance, create market evidence, or decide
scheme eligibility. It explains the compact assessment context supplied by the
frontend and clearly identifies missing evidence.
"""

from __future__ import annotations

import json
import os
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi

from app.schemas.ai import AssistantResponse


class AssistantUnavailable(RuntimeError):
    pass


def _compact_context(context: dict[str, Any]) -> dict[str, Any]:
    """Keep prompts bounded and reject values not useful for an explanation."""
    allowed = {
        "location", "business", "demographics", "competition", "financial",
        "risks", "opportunities", "limitations", "next_actions",
    }
    return {key: value for key, value in context.items() if key in allowed}


def _fallback(language: str) -> AssistantResponse:
    message = (
        "I cannot reach the explanation service right now. Review the evidence labels, "
        "limitations, and next actions in this report; they remain the source of truth."
        if language == "en" else
        "व्याख्या सेवा अभी उपलब्ध नहीं है। रिपोर्ट में दिए गए डेटा लेबल, सीमाएँ और अगले कदम देखें; वही विश्वसनीय आधार हैं।"
    )
    return AssistantResponse(
        answer=message,
        language=language,
        generated_by="safe_fallback",
        limitations=["The assistant did not generate an answer. No new market or financial claim was created."],
    )


def answer_assessment_question(question: str, language: str, context: dict[str, Any]) -> AssistantResponse:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return _fallback(language)
    language_instruction = "Reply in clear Hindi." if language == "hi" else "Reply in clear English."
    prompt = (
        "You are VyaparSathi's explanation assistant. "
        "Explain ONLY the assessment context below. Do not invent population, demand, revenue, prices, "
        "competitor totals, scheme eligibility, or a guarantee. Do not replace deterministic calculations. "
        "If the context marks something unavailable or unknown, say that it needs verification. "
        "Give a short, practical answer with a final 'What to do next' sentence. "
        + language_instruction
        + "\n\nAssessment context:\n"
        + json.dumps(_compact_context(context), ensure_ascii=False, default=str)
        + "\n\nUser question:\n"
        + question
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
    }).encode("utf-8")
    request = Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20, context=ssl.create_default_context(cafile=certifi.where())) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AssistantUnavailable("The explanation service could not complete the request.") from exc
    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    parts = candidates[0].get("content", {}).get("parts", []) if isinstance(candidates, list) and candidates else []
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not text:
        raise AssistantUnavailable("The explanation service returned no usable answer.")
    return AssistantResponse(
        answer=text,
        language=language,
        generated_by="gemini",
        limitations=["AI explanation is grounded only in the displayed assessment context; verify all user inputs and public-data limitations before acting."],
    )
