"""Location-search conveniences. Canonical administrative selection stays local."""

from fastapi import APIRouter

from app.schemas.location import (
    MapplsAutosuggestRequest,
    MapplsAutosuggestResponse,
    MapplsLocationSuggestion,
)
from app.services.location.external_geo import ExternalGeoUnavailable, mappls_autosuggest


router = APIRouter(prefix="/api/location", tags=["Location Assistance"])


@router.post("/autosuggest", response_model=MapplsAutosuggestResponse)
async def autosuggest_location(request: MapplsAutosuggestRequest) -> MapplsAutosuggestResponse:
    try:
        suggestions = mappls_autosuggest(request.query.strip(), request.pod)
    except ExternalGeoUnavailable as exc:
        return MapplsAutosuggestResponse(status="INSUFFICIENT", limitations=[str(exc)])
    return MapplsAutosuggestResponse(
        status="AVAILABLE",
        suggestions=[MapplsLocationSuggestion(
            type=item.type, place_name=item.place_name, place_address=item.place_address,
            alternate_name=item.alternate_name, mappls_eloc=item.eloc,
        ) for item in suggestions],
        limitations=[
            "Mappls suggestions help locate an area, but the local Census hierarchy remains the authoritative State, District and Sub-district selection.",
        ],
    )
