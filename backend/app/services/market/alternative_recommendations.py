"""Evidence-only lower-risk category alternatives for the final report."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.enums import ConfidenceLevel, DataClassification
from app.schemas.business import BusinessCategory
from app.schemas.common import DataProvenance
from app.schemas.market import (
    AlternativeBusinessCategory,
    AlternativeRecommendationRequest,
    AlternativeRecommendationResponse,
)
from app.services.market.live_competitor_mapping import LiveDataUnavailable, OverpassClient, _unique_elements


HIGH_RISK_THRESHOLD = 70


def _categories() -> list[BusinessCategory]:
    path = Path(__file__).resolve().parents[3] / "data" / "business_categories.json"
    try:
        return [BusinessCategory(**item) for item in json.loads(path.read_text(encoding="utf-8"))]
    except (OSError, json.JSONDecodeError):
        return []


def _market_risk_score(mapped_competitor_count: int) -> int:
    """A transparent local supply-pressure score; it never estimates demand."""
    return min(100, max(0, mapped_competitor_count * 10))


def _matches_category(element: dict, category: BusinessCategory) -> bool:
    tags = element.get("tags") if isinstance(element.get("tags"), dict) else {}
    return any(all(tags.get(key) == value for key, value in rule.items()) for rule in category.osm_competitor_tags)


def recommend_lower_risk_categories(
    request: AlternativeRecommendationRequest,
) -> AlternativeRecommendationResponse:
    current_risk = _market_risk_score(request.current_mapped_competitor_count)
    methodology = [
        "Market risk score = 10 points for each mapped comparable business within the selected radius, capped at 100.",
        "Fit score rewards a lower mapped-comparable-business risk score at this exact map point; it is not a demand, revenue, licensing, or profit forecast.",
    ]
    if current_risk < HIGH_RISK_THRESHOLD:
        return AlternativeRecommendationResponse(
            status="AVAILABLE", current_market_risk_score=current_risk, risk_level="NOT_HIGH",
            methodology=methodology,
            limitations=["Alternatives are withheld until the current category has a high local market-risk score."],
        )

    categories = [category for category in _categories() if category.category_id != request.category_id and category.osm_competitor_tags]
    if not categories:
        return AlternativeRecommendationResponse(
            status="INSUFFICIENT", current_market_risk_score=current_risk, risk_level="UNKNOWN",
            methodology=methodology, limitations=["Configured business-category mapping rules are unavailable."],
        )

    all_tags = [tag for category in categories for tag in category.osm_competitor_tags]
    try:
        elements = _unique_elements(OverpassClient().mapped_competitors_nearby(
            request.latitude, request.longitude, request.radius_km, all_tags
        ))
    except LiveDataUnavailable as exc:
        return AlternativeRecommendationResponse(
            status="INSUFFICIENT", current_market_risk_score=current_risk, risk_level="HIGH",
            methodology=methodology, limitations=[str(exc)],
        )

    alternatives: list[AlternativeBusinessCategory] = []
    for category in categories:
        mapped_count = sum(_matches_category(element, category) for element in elements)
        candidate_risk = _market_risk_score(mapped_count)
        if candidate_risk >= current_risk:
            continue
        fit_score = min(99, max(1, round(45 + (current_risk - candidate_risk) * 0.55)))
        alternatives.append(AlternativeBusinessCategory(
            category_id=category.category_id,
            name=category.name,
            mapped_competitor_count=mapped_count,
            market_risk_score=candidate_risk,
            fit_score=fit_score,
        ))

    alternatives.sort(key=lambda item: (-item.fit_score, item.mapped_competitor_count, item.name.casefold()))
    return AlternativeRecommendationResponse(
        status="AVAILABLE", current_market_risk_score=current_risk, risk_level="HIGH",
        alternatives=alternatives[:3],
        methodology=methodology + [
            "Alternative counts are live OpenStreetMap features matched to each category's documented mapping tags within the selected radius.",
        ],
        limitations=[
            "Mapped businesses are observed features, not a complete register of formal or informal competitors.",
            "The current category may include other verified mapping providers, while alternatives use a single comparable OpenStreetMap lookup.",
            "Validate demand, operating skills, supplier access, permissions, and prices locally before changing category.",
        ],
        data_provenance=[DataProvenance(
            source_id="OSM_OVERPASS_LIVE", source_name="OpenStreetMap via Overpass API",
            source_url="https://www.openstreetmap.org/", data_type=DataClassification.VERIFIED,
            confidence=ConfidenceLevel.MEDIUM,
            notes="Live mapped features near the selected analysis point; mapping coverage varies by area.",
        )],
    )
