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
    messages = {
        "en": "I cannot reach the explanation service right now. Review the evidence labels, limitations, and next actions in this report; they remain the source of truth.",
        "hi": "व्याख्या सेवा अभी उपलब्ध नहीं है। रिपोर्ट में दिए गए डेटा लेबल, सीमाएँ और अगले कदम देखें; वही विश्वसनीय आधार हैं।",
        "bn": "ব্যাখ্যা পরিষেবা এখন পাওয়া যাচ্ছে না। রিপোর্টের প্রমাণ লেবেল, সীমাবদ্ধতা এবং পরবর্তী পদক্ষেপ দেখুন; সেগুলিই সত্যের ভিত্তি।",
        "mr": "स्पष्टीकरण सेवा आत्ता उपलब्ध नाही. अहवालातील पुरावा लेबल, मर्यादा आणि पुढील कृती तपासा; तीच विश्वसनीय आधार आहेत.",
        "ta": "விளக்கம் சேவை இப்போது கிடைக்கவில்லை. அறிக்கையில் உள்ள ஆதார லேபிள்கள், வரம்புகள் மற்றும் அடுத்த படிகளை பார்க்கவும்; அவையே நம்பகமான அடிப்படை.",
    }
    message = messages.get(language, messages["en"])
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
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    language_instruction = {
        "en": "Reply in clear English.",
        "hi": "Reply in clear Hindi.",
        "bn": "Reply in clear Bengali.",
        "mr": "Reply in clear Marathi.",
        "ta": "Reply in clear Tamil.",
    }.get(language, "Reply in clear English.")
    prompt = (
        "You are VyaparSathi's explanation assistant. "
        "Explain ONLY the assessment context below. Do not invent population, demand, revenue, prices, "
        "competitor totals, scheme eligibility, or a guarantee. Do not replace deterministic calculations. "
        "If the context marks something unavailable or unknown, say that it needs verification. "
        "Start with the direct answer, then give the relevant evidence and a final 'What to do next' sentence. "
        "Use one complete plain-text paragraph of 50 to 90 words; do not use Markdown, headings, bullet points, or unfinished sentences. "
        + language_instruction
        + "\n\nAssessment context:\n"
        + json.dumps(_compact_context(context), ensure_ascii=False, default=str)
        + "\n\nUser question:\n"
        + question
    )
    def generate(instruction: str) -> str:
        body = json.dumps({
            "contents": [{"parts": [{"text": instruction}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1600},
        }).encode("utf-8")
        request = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
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
        return "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()

    text = generate(prompt)
    # Some provider/model combinations can end an otherwise successful response
    # mid-sentence. Continue only those incomplete responses, retaining the same
    # constrained context and never fabricating a local fact.
    for _ in range(3):
        if text.endswith((".", "!", "?", "।")) and len(text.split()) >= 35:
            break
        continuation = generate(
            prompt + "\n\nPartial answer already shown to the user:\n" + text
            + "\n\nContinue from the exact last word without repeating it. Finish the current sentence and provide the remaining concise answer. End with punctuation."
        )
        if not continuation:
            break
        text = f"{text} {continuation}".strip()
    if not text:
        raise AssistantUnavailable("The explanation service returned no usable answer.")
    first_next_step = text.lower().find("what to do next")
    if first_next_step >= 0:
        first_next_sentence_end = text.find(".", first_next_step)
        if first_next_sentence_end >= 0:
            text = text[:first_next_sentence_end + 1]
    if any(marker in text for marker in ("Assessment context:", "User question:", " -> ", "\n    - ")):
        raise AssistantUnavailable("The explanation service returned malformed content.")
    return AssistantResponse(
        answer=text,
        language=language,
        generated_by="gemini",
        limitations=["AI explanation is grounded only in the displayed assessment context; verify all user inputs and public-data limitations before acting."],
    )
