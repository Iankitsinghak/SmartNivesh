"""Optional, key-backed geographic providers with bounded calls and no secret exposure."""

from __future__ import annotations

import json
import os
import ssl
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi


class ExternalGeoUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class MapplsSuggestion:
    type: str
    place_name: str
    place_address: Optional[str]
    alternate_name: Optional[str]
    eloc: str


def _enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def _json_request(url: str, *, headers: Optional[dict[str, str]] = None,
                  body: Optional[dict[str, Any]] = None, timeout: float = 8) -> dict[str, Any]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=payload, headers=request_headers, method="POST" if payload else "GET")
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=timeout, context=context) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ExternalGeoUnavailable("The configured geographic provider could not complete the request.") from exc
    if not isinstance(result, dict):
        raise ExternalGeoUnavailable("The configured geographic provider returned an invalid response.")
    return result


@dataclass(frozen=True)
class GeocodedPoint:
    latitude: float
    longitude: float
    provider: str
    source_id: Optional[str] = None


@lru_cache(maxsize=4096)
def geocode_administrative_area(state: str, district: str, subdistrict: str) -> GeocodedPoint:
    query = f"{subdistrict}, {district}, {state}, India"
    google_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if google_key and _enabled("VYAPARSATHI_GOOGLE_MAPS_ENABLED"):
        url = "https://maps.googleapis.com/maps/api/geocode/json?" + urlencode({
            "address": query, "region": "in", "key": google_key,
        })
        result = _json_request(url)
        matches = result.get("results") if isinstance(result.get("results"), list) else []
        if matches:
            location = matches[0].get("geometry", {}).get("location", {})
            if location.get("lat") is not None and location.get("lng") is not None:
                return GeocodedPoint(
                    float(location["lat"]), float(location["lng"]), "Google Geocoding",
                    str(matches[0].get("place_id")) if matches[0].get("place_id") else None,
                )

    ors_key = os.getenv("OPENROUTESERVICE_API_KEY")
    if ors_key and _enabled("VYAPARSATHI_OPENROUTESERVICE_ENABLED"):
        url = "https://api.heigit.org/pelias/v1/search?" + urlencode({
            "api_key": ors_key, "text": query, "boundary.country": "IND", "size": 1,
        })
        result = _json_request(url)
        features = result.get("features") if isinstance(result.get("features"), list) else []
        if features:
            coordinates = features[0].get("geometry", {}).get("coordinates", [])
            if len(coordinates) >= 2:
                return GeocodedPoint(float(coordinates[1]), float(coordinates[0]), "openrouteservice")
    raise ExternalGeoUnavailable("No configured provider could resolve this administrative area.")


def google_places_for_category(category_name: str, latitude: float, longitude: float,
                               state: str, district: str, subdistrict: str) -> list[dict[str, Any]]:
    key = os.getenv("VYAPARSATHI_GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
    if not key or (not os.getenv("VYAPARSATHI_GOOGLE_PLACES_API_KEY") and not _enabled("VYAPARSATHI_GOOGLE_MAPS_ENABLED")):
        raise ExternalGeoUnavailable("Google Places fallback is not configured.")
    result = _json_request(
        "https://places.googleapis.com/v1/places:searchText",
        headers={
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,places.businessStatus",
        },
        body={
            "textQuery": f"{category_name} in {subdistrict}, {district}, {state}, India",
            "pageSize": 20,
            "locationBias": {"circle": {
                "center": {"latitude": latitude, "longitude": longitude}, "radius": 10000.0,
            }},
        },
    )
    places = result.get("places") if isinstance(result.get("places"), list) else []
    return [item for item in places if isinstance(item, dict) and item.get("businessStatus") != "CLOSED_PERMANENTLY"]


_GEOAPIFY_CATEGORIES = {
    "Restaurant": "catering.restaurant,catering.fast_food",
    "Hotel": "accommodation.hotel",
    "Cosmetics": "commercial.beauty",
    "Kirana / General Store": "commercial.supermarket,commercial.convenience",
    "Tea & Snack Stall": "catering.cafe,catering.fast_food",
    "Bakery": "catering.cafe,commercial.food_and_drink",
    "Tailoring & Boutique": "commercial.clothing",
    "Beauty Salon": "commercial.beauty",
    "Mobile Phone Shop & Repair": "commercial.elektronics",
    "Pharmacy / Medical Store": "healthcare.pharmacy",
    "Fruit & Vegetable Shop": "commercial.food_and_drink",
    "Dairy / Milk Shop": "commercial.food_and_drink",
    "Stationery & Photocopy": "commercial.stationery",
    "Hardware & Electrical Store": "commercial.hardware,commercial.elektronics",
    "Furniture & Carpentry": "commercial.furniture,commercial.wood",
    "Welding & Fabrication": "commercial.industrial",
    "Laundry & Ironing": "service.laundry",
    "Bicycle Sales & Repair": "commercial.bicycle,service.vehicle.bicycle",
    "Agricultural Input Store": "commercial.garden",
    "Textiles & Garment Store": "commercial.clothing",
    "Footwear Store & Repair": "commercial.shoes,service.shoes",
    "Computer & Digital Service Centre": "commercial.elektronics,service.financial",
}


def geoapify_places_for_category(category_name: str, latitude: float, longitude: float) -> list[dict[str, Any]]:
    """Fetch nearby OSM-derived POIs from Geoapify as a bounded live fallback."""
    key = os.getenv("GEOAPIFY_API_KEY")
    categories = _GEOAPIFY_CATEGORIES.get(category_name)
    if not key or not categories:
        raise ExternalGeoUnavailable("Geoapify Places fallback is not configured for this business category.")
    result = _json_request("https://api.geoapify.com/v2/places?" + urlencode({
        "categories": categories, "filter": f"circle:{longitude},{latitude},10000",
        "bias": f"proximity:{longitude},{latitude}", "limit": 100, "apiKey": key,
    }))
    features = result.get("features") if isinstance(result.get("features"), list) else []
    return [feature for feature in features if isinstance(feature, dict)]


@dataclass(frozen=True)
class RouteSummary:
    distance_km: float
    duration_minutes: float
    provider: str = "openrouteservice"


@lru_cache(maxsize=4096)
def route_summary(origin_lat: float, origin_lon: float, destination_lat: float, destination_lon: float) -> RouteSummary:
    key = os.getenv("OPENROUTESERVICE_API_KEY")
    if not key or not _enabled("VYAPARSATHI_OPENROUTESERVICE_ENABLED"):
        raise ExternalGeoUnavailable("openrouteservice is not configured.")
    url = "https://api.heigit.org/openrouteservice/v2/directions/driving-car/geojson"
    result = _json_request(
        url, headers={"Authorization": key, "Accept": "application/geo+json"},
        body={"coordinates": [[origin_lon, origin_lat], [destination_lon, destination_lat]]},
    )
    features = result.get("features") if isinstance(result.get("features"), list) else []
    summary = features[0].get("properties", {}).get("summary", {}) if features else {}
    if summary.get("distance") is None or summary.get("duration") is None:
        raise ExternalGeoUnavailable("openrouteservice returned no route for these coordinates.")
    return RouteSummary(float(summary["distance"]) / 1000, float(summary["duration"]) / 60)


@lru_cache(maxsize=1024)
def mappls_autosuggest(query: str, pod: Optional[str] = None) -> tuple[MapplsSuggestion, ...]:
    """Return normalized Mappls search suggestions without exposing its token.

    Autosuggest is a convenience search layer only. The Census hierarchy remains
    the authoritative selection source because Mappls does not return LGD codes
    or stable parent-child administrative identifiers.
    """
    token = os.getenv("MAPPLS_ACCESS_TOKEN")
    if not token:
        raise ExternalGeoUnavailable("Mappls location search is not configured.")
    params = {"query": query, "access_token": token}
    if pod:
        params["pod"] = pod
    result = _json_request(
        "https://search.mappls.com/search/places/autosuggest/json?" + urlencode(params),
        timeout=8,
    )
    raw_suggestions = result.get("suggestedLocations")
    if not isinstance(raw_suggestions, list):
        raise ExternalGeoUnavailable("Mappls returned an invalid location-search response.")
    allowed_types = {"STATE", "DISTRICT", "SUB_DISTRICT", "VILLAGE"}
    suggestions: list[MapplsSuggestion] = []
    for item in raw_suggestions[:12]:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type", "")).upper()
        name = item.get("placeName")
        eloc = item.get("eLoc")
        if item_type not in allowed_types or not isinstance(name, str) or not isinstance(eloc, str):
            continue
        suggestions.append(MapplsSuggestion(
            type=item_type,
            place_name=name,
            place_address=item.get("placeAddress") if isinstance(item.get("placeAddress"), str) else None,
            alternate_name=item.get("alternateName") if isinstance(item.get("alternateName"), str) else None,
            eloc=eloc,
        ))
    return tuple(suggestions)
