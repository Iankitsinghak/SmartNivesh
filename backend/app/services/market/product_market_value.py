"""Verified MPCE-based local price positioning for micro-enterprises.

There is no single Government of India price series that can truthfully price
restaurants, salons, tailoring, repair work, and retail goods across every
Indian block. This adapter therefore does not configure or call a generic
market-price API. It uses the official MoSPI HCES rural MPCE table to produce
one transparent affordability multiplier that works for every supported
category:

    state rural MPCE / All-India rural MPCE

When the entrepreneur supplies an actual comparable reference price, the same
multiplier produces a local planning reference. The result is explicitly a
calculation, never an observed market price or a claim of the optimal price.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.core.enums import ConfidenceLevel, DataClassification
from app.schemas.common import DataProvenance
from app.schemas.market import (
    PricingRecommendation,
    ProductMarketValueRequest,
    ProductMarketValueResponse,
    PurchasingPowerContext,
)
from app.services.market.live_competitor_mapping import (
    LiveDataUnavailable,
    _data_path,
    _load_category,
    _normalise_text,
)


@dataclass(frozen=True)
class RegionalPurchasingPower:
    index: float
    baseline: float
    geographic_scope: str
    observed_at: Optional[str]
    source_name: str
    source_url: str
    source_id: str = "PUBLIC_PURCHASING_POWER"
    basis: Optional[str] = None


MPCE_RESOURCE_ID = "89bf5d50-cecf-4219-84d9-12b062c301e2"
MPCE_SOURCE_NAME = "MoSPI HCES 2023-24 rural MPCE via data.gov.in"
_STATE_NAME_ALIASES = {
    "andaman and nicobar islands": "Andaman & Nicobar Islands",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "jammu and kashmir": "Jammu & Kashmir",
    "national capital territory of delhi": "Delhi",
    "nct of delhi": "Delhi",
    "orissa": "Odisha",
    "pondicherry": "Puducherry",
}


def _positive_number(value: object, field_name: str) -> float:
    try:
        result = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError) as exc:
        raise LiveDataUnavailable(f"The official HCES table has an invalid {field_name} value.") from exc
    if result <= 0:
        raise LiveDataUnavailable(f"The official HCES table has a non-positive {field_name} value.")
    return result


class PublicPurchasingPowerApi:
    """State rural-MPCE proxy from an exact reviewed Government of India resource.

    data.gov.in marks the source API as unavailable, so the checked-in table is
    a versioned transcription of the official 2023-24 HCES release. The exact
    resource UUID and source page remain in every response for auditability.
    """

    def __init__(self) -> None:
        try:
            payload = json.loads(_data_path("india_hces_2023_24_mpce.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LiveDataUnavailable("The reviewed Government of India MPCE snapshot is unavailable.") from exc
        if payload.get("data_gov_resource_id") != MPCE_RESOURCE_ID:
            raise LiveDataUnavailable("The reviewed MPCE snapshot has an unexpected resource identifier.")
        values = payload.get("values")
        if not isinstance(values, dict):
            raise LiveDataUnavailable("The reviewed MPCE snapshot has no state records.")
        self.payload = payload
        self.values = values

    def fetch(self, request: ProductMarketValueRequest) -> RegionalPurchasingPower:
        requested = _normalise_text(request.state_name)
        canonical_name = _STATE_NAME_ALIASES.get(requested)
        if canonical_name is None:
            canonical_name = next(
                (name for name in self.values if _normalise_text(name) == requested),
                None,
            )
        state_record = self.values.get(canonical_name) if canonical_name else None
        baseline_record = self.values.get("All-India")
        if not isinstance(state_record, dict) or not isinstance(baseline_record, dict):
            raise LiveDataUnavailable(
                "The official 2023-24 HCES table has no rural MPCE record for the selected state."
            )
        state_mpce = _positive_number(state_record.get("rural"), "state rural MPCE")
        all_india_mpce = _positive_number(baseline_record.get("rural"), "All-India rural MPCE")
        return RegionalPurchasingPower(
            index=state_mpce,
            baseline=all_india_mpce,
            geographic_scope="state (rural)",
            observed_at=str(self.payload.get("reference_period") or "2023-24"),
            source_name=MPCE_SOURCE_NAME,
            source_url=str(self.payload["data_gov_resource_url"]),
            source_id=MPCE_RESOURCE_ID,
            basis=(
                "Average rural MPCE compared with the All-India rural MPCE. "
                "This is a consumption-expenditure proxy, not an observed local price."
            ),
        )


def _provenance(purchasing_power: RegionalPurchasingPower) -> DataProvenance:
    return DataProvenance(
        source_id=purchasing_power.source_id,
        source_name=purchasing_power.source_name,
        source_url=purchasing_power.source_url,
        data_type=DataClassification.VERIFIED,
        last_verified=datetime.now(timezone.utc),
        confidence=ConfidenceLevel.MEDIUM,
        notes=(
            "Official data.gov.in resource UUID retained. State rural MPCE is divided by "
            "the All-India rural MPCE; this is a state-level affordability proxy, not a block estimate."
        ),
    )


def _insufficient(request: ProductMarketValueRequest, message: str) -> ProductMarketValueResponse:
    return ProductMarketValueResponse(
        status="INSUFFICIENT",
        category_id=request.category_id,
        state_name=request.state_name,
        district_name=request.district_name,
        block_name=request.block_name,
        confidence=ConfidenceLevel.LOW,
        limitations=[message, "No seeded, scraped, or synthetic price was used for this result."],
    )


def analyze_product_market_value(request: ProductMarketValueRequest) -> ProductMarketValueResponse:
    """Return an official-data affordability multiplier for every mapped category."""

    if _load_category(request.category_id) is None:
        return _insufficient(request, "Business category not found.")
    try:
        purchasing_power = PublicPurchasingPowerApi().fetch(request)
    except LiveDataUnavailable as exc:
        return _insufficient(request, str(exc))

    adjustment_factor = purchasing_power.index / purchasing_power.baseline
    reference_price = request.reference_price
    adjusted_reference_price = (
        round(reference_price * adjustment_factor, 2) if reference_price is not None else None
    )
    power_context = PurchasingPowerContext(
        index=purchasing_power.index,
        baseline=purchasing_power.baseline,
        geographic_scope=purchasing_power.geographic_scope,
        observed_at=purchasing_power.observed_at,
        basis=purchasing_power.basis,
    )
    recommendation = PricingRecommendation(
        adjustment_factor=round(adjustment_factor, 4),
        relative_position_percent=round(adjustment_factor * 100, 1),
        reference_price=reference_price,
        adjusted_reference_price=adjusted_reference_price,
        strategy=(
            "Use the affordability multiplier to position a comparable price slightly above the "
            "All-India rural reference level."
            if adjustment_factor >= 1
            else "Use the affordability multiplier to position a comparable price below the "
            "All-India rural reference level."
        ),
    )
    methodology = [
        "The selected state's official 2023-24 rural MPCE is divided by the All-India rural MPCE.",
        "Affordability multiplier = state rural MPCE / All-India rural MPCE.",
    ]
    if reference_price is not None:
        methodology.append(
            "MPCE-adjusted planning reference = entrepreneur-entered comparable price × affordability multiplier."
        )
    else:
        methodology.append(
            "No reference price was entered, so the result is shown as a percentage multiplier rather than an invented rupee price."
        )

    return ProductMarketValueResponse(
        status="AVAILABLE",
        category_id=request.category_id,
        state_name=request.state_name,
        district_name=request.district_name,
        block_name=request.block_name,
        purchasing_power=power_context,
        recommendation=recommendation,
        confidence=ConfidenceLevel.MEDIUM,
        methodology=methodology,
        limitations=[
            "This is an MPCE-based affordability calculation, not an observed market price, demand forecast, or guarantee of an optimal price.",
            "MPCE is a state-level rural consumption-expenditure proxy; it is not block-level willingness to pay.",
            "Any reference price is supplied by the entrepreneur and must be supported by a current quotation, menu, or comparable local offer before use.",
        ],
        data_provenance=[_provenance(purchasing_power)],
    )
