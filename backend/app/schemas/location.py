from pydantic import BaseModel, Field
from typing import Literal, Optional

class LocationHierarchy(BaseModel):
    country: str = "India"
    state: str
    district: str
    block: Optional[str] = None
    village_town: str

class Location(BaseModel):
    location_id: str
    latitude: float
    longitude: float
    hierarchy: LocationHierarchy


class MapplsAutosuggestRequest(BaseModel):
    """Server-side location-search request. The Mappls token is never accepted here."""

    query: str = Field(min_length=2, max_length=160)
    pod: Optional[Literal["STATE", "DIST", "SDIST", "VLG"]] = None


class MapplsLocationSuggestion(BaseModel):
    type: Literal["STATE", "DISTRICT", "SUB_DISTRICT", "VILLAGE"]
    place_name: str
    place_address: Optional[str] = None
    alternate_name: Optional[str] = None
    mappls_eloc: str


class MapplsAutosuggestResponse(BaseModel):
    status: Literal["AVAILABLE", "INSUFFICIENT"]
    suggestions: list[MapplsLocationSuggestion] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
