"""Evidence-gated competitor mapping backed by official public records.

This module deliberately does not read ``data/businesses.json`` or
``data/demographics.json``. A result is available only when the requested
block can be verified in OpenStreetMap and the Census of India Village
Amenities files contain matching state, district, and CD-block rows.
"""

from __future__ import annotations

import json
import os
import csv
import io
import base64
import re
import ssl
from concurrent.futures import ThreadPoolExecutor
import unicodedata
from threading import Lock
from time import monotonic
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from app.core.enums import ConfidenceLevel, DataClassification
from app.schemas.business import BusinessCategory
from app.schemas.common import DataProvenance
from app.schemas.market import (
    CompetitorMappingRequest,
    CompetitorMappingResponse,
    DemographicMappingContext,
    EconomicMappingContext,
    IndiaAdministrativeOption,
    IndiaAdministrativeOptionsResponse,
    MappedCompetitor,
)


DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
SECONDARY_OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"
OSM_SOURCE_URL = "https://www.openstreetmap.org/"
MAX_RETURNED_COMPETITORS = 100
CENSUS_VILLAGE_AMENITIES_CATALOG_ID = "007f2c63-cdb1-4c91-82ef-61716f0b0e76"
CENSUS_VILLAGE_AMENITIES_CATALOG_URL = (
    "https://www.data.gov.in/catalog/village-amenities-census-2011"
)
CENSUS_RESOURCE_PREFIX = "https://www.data.gov.in/resource/"
CENSUS_SOURCE_NAME = "Census of India 2011 Village Amenities"
MAX_CENSUS_CSV_BYTES = 50 * 1024 * 1024

# Canonical Government of India State/UT labels used by the instant client-side
# directory.  A `state:<slug>` is not an OSM identifier; it is resolved within
# the Overpass query, avoiding a separate state-list request before districts.
_INDIA_STATE_NAMES = {
    "andaman-and-nicobar-islands": "Andaman and Nicobar Islands",
    "andhra-pradesh": "Andhra Pradesh", "arunachal-pradesh": "Arunachal Pradesh",
    "assam": "Assam", "bihar": "Bihar", "chandigarh": "Chandigarh",
    "chhattisgarh": "Chhattisgarh", "dadra-and-nagar-haveli-and-daman-and-diu": "Dadra and Nagar Haveli and Daman and Diu",
    "delhi": "Delhi", "goa": "Goa", "gujarat": "Gujarat", "haryana": "Haryana",
    "himachal-pradesh": "Himachal Pradesh", "jammu-and-kashmir": "Jammu and Kashmir",
    "jharkhand": "Jharkhand", "karnataka": "Karnataka", "kerala": "Kerala",
    "ladakh": "Ladakh", "lakshadweep": "Lakshadweep", "madhya-pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra", "manipur": "Manipur", "meghalaya": "Meghalaya",
    "mizoram": "Mizoram", "nagaland": "Nagaland", "odisha": "Odisha",
    "puducherry": "Puducherry", "punjab": "Punjab", "rajasthan": "Rajasthan",
    "sikkim": "Sikkim", "tamil-nadu": "Tamil Nadu", "telangana": "Telangana",
    "tripura": "Tripura", "uttar-pradesh": "Uttar Pradesh", "uttarakhand": "Uttarakhand",
    "west-bengal": "West Bengal",
}


@dataclass(frozen=True)
class _AdministrativeCacheEntry:
    options: tuple[IndiaAdministrativeOption, ...]
    retrieved_at: datetime
    expires_at: float


_ADMINISTRATIVE_OPTIONS_CACHE: dict[str, _AdministrativeCacheEntry] = {}
_ADMINISTRATIVE_OPTIONS_CACHE_LOCK = Lock()


class LiveDataUnavailable(RuntimeError):
    """Raised only for an evidence gap or public-source failure."""


@dataclass(frozen=True)
class BlockBoundary:
    osm_area_id: int
    name: str
    admin_level: Optional[str]


@dataclass(frozen=True)
class DemographicSnapshot:
    total_population: int
    households: Optional[int]
    working_population: Optional[int]
    segments: dict[str, int]
    source_name: str
    source_url: str
    source_id: str = "PUBLIC_BLOCK_DEMOGRAPHICS"
    source_notes: Optional[str] = None


@dataclass(frozen=True)
class _CensusDistrictCacheEntry:
    records: tuple[dict[str, str], ...]
    resource_id: str
    resource_url: str
    retrieved_at: datetime
    expires_at: float
    retrieval_note: Optional[str] = None


_CENSUS_DISTRICT_CACHE: dict[str, _CensusDistrictCacheEntry] = {}
_CENSUS_DISTRICT_CACHE_LOCK = Lock()


def _data_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[3] / "data" / filename


def _configured_https_url(variable_name: str, default: Optional[str] = None) -> str:
    value = os.getenv(variable_name, default)
    if not value:
        raise LiveDataUnavailable(f"{variable_name} is not configured.")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise LiveDataUnavailable(f"{variable_name} must be an HTTPS URL.")
    return value


def _public_source_url(url: str) -> str:
    """Do not expose query parameters, which can contain an API key."""

    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def _fetch_json(
    url: str, *, payload: Optional[str] = None, timeout_seconds: Optional[float] = None
) -> dict[str, Any]:
    timeout = timeout_seconds if timeout_seconds is not None else float(
        os.getenv("VYAPARSATHI_PUBLIC_DATA_TIMEOUT_SECONDS", "30")
    )
    headers = {
        "Accept": "application/json",
        "User-Agent": os.getenv(
            "VYAPARSATHI_HTTP_USER_AGENT",
            "VyaparSathi/1.0 (public-data competitor mapping)",
        ),
    }
    request = Request(
        url,
        data=payload.encode("utf-8") if payload is not None else None,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310 - HTTPS endpoint is validated above
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LiveDataUnavailable("A required public data source could not be retrieved.") from exc


def _fetch_public_bytes(url: str, *, accept: str, maximum_bytes: int) -> bytes:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise LiveDataUnavailable("A Government of India data URL was not HTTPS.")
    timeout = float(os.getenv("VYAPARSATHI_CENSUS_DATA_TIMEOUT_SECONDS", "45"))
    request = Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": os.getenv(
                "VYAPARSATHI_HTTP_USER_AGENT",
                "VyaparSathi/1.0 (public-data competitor mapping)",
            ),
        },
        method="GET",
    )
    try:
        with urlopen(  # nosec B310 - HTTPS is required above
            request, timeout=timeout, context=_windows_trust_context()
        ) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > maximum_bytes:
                raise LiveDataUnavailable("The official Census district file exceeds the safety limit.")
            content = response.read(maximum_bytes + 1)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise LiveDataUnavailable("The official Government of India data file could not be retrieved.") from exc
    if len(content) > maximum_bytes:
        raise LiveDataUnavailable("The official Census district file exceeds the safety limit.")
    return content


def _local_census_cache_file(file_url: str) -> Optional[Path]:
    """Find a locally cached copy of the exact official file, if configured."""
    cache_dir = os.getenv("VYAPARSATHI_CENSUS_LOCAL_CACHE_DIR")
    if not cache_dir:
        return None
    filename = Path(urlsplit(file_url).path).name
    candidate = Path(cache_dir).expanduser() / filename
    if candidate.is_file():
        return candidate
    return None


def _windows_trust_context() -> ssl.SSLContext:
    """Use the host Windows trust store when Python's bundle lacks its roots.

    This keeps normal certificate and hostname verification enabled.  The
    Census host is an official HTTPS source whose chain is trusted by Windows
    but is not present in the bundled Python CA file on some deployments.
    """
    context = ssl.create_default_context()
    if os.name != "nt" or not hasattr(ssl, "enum_certificates"):
        return context
    certificates: list[str] = []
    for certificate, encoding, _trust in ssl.enum_certificates("ROOT"):
        if encoding != "x509_asn":
            continue
        certificates.append(
            "-----BEGIN CERTIFICATE-----\n"
            + base64.b64encode(certificate).decode("ascii")
            + "\n-----END CERTIFICATE-----"
        )
    if certificates:
        context.load_verify_locations(cadata="\n".join(certificates))
    return context


def _ql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _normalise_text(value: object) -> str:
    return " ".join(str(value).casefold().split())


def _normalise_geography(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.casefold().replace("&", " and ")).split())


def _slugify_geography(value: str) -> str:
    return _normalise_geography(value).replace(" ", "-")


def _normalise_district(value: object) -> str:
    normalized = _normalise_geography(value)
    return normalized[:-9].strip() if normalized.endswith(" district") else normalized


def _normalise_block(value: object) -> str:
    """Align Census CD-block labels with OSM Taluka/Subdistrict labels."""
    normalized = _normalise_geography(value)
    for suffix in (" taluka", " subdistrict", " tehsil", " tahsil"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)].strip()
    return normalized


def _block_admin_level_pattern() -> str:
    raw_levels = os.getenv("VYAPARSATHI_BLOCK_ADMIN_LEVELS", "6,7")
    levels = [level.strip() for level in raw_levels.split(",") if level.strip()]
    if not levels or any(not level.isdigit() or not 1 <= int(level) <= 11 for level in levels):
        raise LiveDataUnavailable(
            "VYAPARSATHI_BLOCK_ADMIN_LEVELS must be a comma-separated list of OSM admin levels."
        )
    return "^(" + "|".join(levels) + ")$"


def _administrative_cache_key(level: str, parent_id: Optional[str]) -> str:
    return f"{level}:{parent_id or ''}"


def _administrative_cache_ttl_seconds(level: str) -> float:
    defaults = {"state": 7 * 24 * 60 * 60, "district": 24 * 60 * 60, "block": 6 * 60 * 60}
    configured = os.getenv(f"VYAPARSATHI_{level.upper()}_ADMIN_CACHE_TTL_SECONDS")
    try:
        ttl = float(configured) if configured is not None else defaults[level]
    except (TypeError, ValueError) as exc:
        raise LiveDataUnavailable(
            f"VYAPARSATHI_{level.upper()}_ADMIN_CACHE_TTL_SECONDS must be a number."
        ) from exc
    if ttl < 0:
        raise LiveDataUnavailable(
            f"VYAPARSATHI_{level.upper()}_ADMIN_CACHE_TTL_SECONDS must not be negative."
        )
    return ttl


def _cached_administrative_options(
    level: str, parent_id: Optional[str]
) -> Optional[_AdministrativeCacheEntry]:
    key = _administrative_cache_key(level, parent_id)
    with _ADMINISTRATIVE_OPTIONS_CACHE_LOCK:
        entry = _ADMINISTRATIVE_OPTIONS_CACHE.get(key)
        if entry and entry.expires_at > monotonic():
            return entry
        if entry:
            del _ADMINISTRATIVE_OPTIONS_CACHE[key]
    return None


def _cache_administrative_options(
    level: str, parent_id: Optional[str], options: list[IndiaAdministrativeOption]
) -> _AdministrativeCacheEntry:
    entry = _AdministrativeCacheEntry(
        options=tuple(options),
        retrieved_at=datetime.now(timezone.utc),
        expires_at=monotonic() + _administrative_cache_ttl_seconds(level),
    )
    with _ADMINISTRATIVE_OPTIONS_CACHE_LOCK:
        _ADMINISTRATIVE_OPTIONS_CACHE[_administrative_cache_key(level, parent_id)] = entry
    return entry


def clear_administrative_options_cache() -> None:
    """Clear live administrative results; used for tests and deliberate cache invalidation."""

    with _ADMINISTRATIVE_OPTIONS_CACHE_LOCK:
        _ADMINISTRATIVE_OPTIONS_CACHE.clear()


def clear_census_district_cache() -> None:
    """Clear downloaded Census district records; used by tests and deliberate refreshes."""

    with _CENSUS_DISTRICT_CACHE_LOCK:
        _CENSUS_DISTRICT_CACHE.clear()


def _area_id_from_reference(reference: str) -> int:
    try:
        object_type, raw_id = reference.split(":", 1)
        object_id = int(raw_id)
    except (ValueError, TypeError) as exc:
        raise LiveDataUnavailable("The parent administrative-area identifier is invalid.") from exc
    if object_id <= 0:
        raise LiveDataUnavailable("The parent administrative-area identifier is invalid.")
    if object_type == "relation":
        return 3_600_000_000 + object_id
    if object_type == "way":
        return 2_400_000_000 + object_id
    if object_type == "area":
        return object_id
    raise LiveDataUnavailable("The parent administrative-area type is unsupported.")


def _to_int(value: object, field_name: str) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        parsed = int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError) as exc:
        raise LiveDataUnavailable(f"The official Census record contains an invalid {field_name} value.") from exc
    if parsed < 0:
        raise LiveDataUnavailable(f"The official Census record contains a negative {field_name} value.")
    return parsed


def _load_category(category_id: str) -> Optional[BusinessCategory]:
    try:
        for item in json.loads(_data_path("business_categories.json").read_text(encoding="utf-8")):
            if item.get("category_id") == category_id:
                return BusinessCategory(**item)
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _osm_provenance(last_verified: Optional[datetime] = None) -> DataProvenance:
    return DataProvenance(
        source_id="OSM_OVERPASS_LIVE",
        source_name="OpenStreetMap via Overpass API",
        source_url=OSM_SOURCE_URL,
        data_type=DataClassification.VERIFIED,
        last_verified=last_verified or datetime.now(timezone.utc),
        confidence=ConfidenceLevel.MEDIUM,
        notes="Live mapped features; mapping coverage varies by block and is not a business census.",
    )


class PublicDemographicsApi:
    """Aggregate Census 2011 village rows for one exact district and CD block.

    The data.gov.in Village Amenities catalog has one directly hosted Census
    CSV per district and does not expose one nationwide row API. The adapter
    resolves the deterministic district resource page, verifies its catalog
    UUID and exact resource UUID, then caches the official Census CSV.
    """

    _state_slug_aliases = {
        "national-capital-territory-of-delhi": "delhi",
        "nct-of-delhi": "delhi",
        "orissa": "odisha",
        "pondicherry": "puducherry",
    }
    _state_data_aliases = {
        "national capital territory of delhi": "delhi",
        "nct of delhi": "delhi",
        "orissa": "odisha",
        "pondicherry": "puducherry",
    }

    def _resource_page_url(self, request: CompetitorMappingRequest) -> str:
        state_slug = _slugify_geography(request.state_name)
        state_slug = self._state_slug_aliases.get(state_slug, state_slug)
        district_slug = _normalise_district(request.district_name).replace(" ", "-")
        return (
            f"{CENSUS_RESOURCE_PREFIX}village-amenities-{district_slug}-district-"
            f"{state_slug}-2011"
        )

    def _cache_ttl_seconds(self) -> float:
        try:
            ttl = float(os.getenv("VYAPARSATHI_CENSUS_DISTRICT_CACHE_TTL_SECONDS", "2592000"))
        except ValueError as exc:
            raise LiveDataUnavailable("VYAPARSATHI_CENSUS_DISTRICT_CACHE_TTL_SECONDS must be a number.") from exc
        if ttl < 0:
            raise LiveDataUnavailable("VYAPARSATHI_CENSUS_DISTRICT_CACHE_TTL_SECONDS must not be negative.")
        return ttl

    def _district_records(self, request: CompetitorMappingRequest) -> _CensusDistrictCacheEntry:
        key = _normalise_geography(request.state_name) + ":" + _normalise_district(request.district_name)
        with _CENSUS_DISTRICT_CACHE_LOCK:
            cached = _CENSUS_DISTRICT_CACHE.get(key)
            if cached and cached.expires_at > monotonic():
                return cached
            if cached:
                del _CENSUS_DISTRICT_CACHE[key]

        resource_url = self._resource_page_url(request)
        html = _fetch_public_bytes(resource_url, accept="text/html", maximum_bytes=5 * 1024 * 1024).decode(
            "utf-8", errors="strict"
        )
        if CENSUS_VILLAGE_AMENITIES_CATALOG_ID not in html:
            raise LiveDataUnavailable(
                "data.gov.in did not resolve the selected district to the reviewed Village Amenities catalog."
            )
        resource_match = re.search(r'uuid:"([0-9a-f-]{36})"', html)
        file_match = re.search(r'field_datafile_url:"([^"]+\.csv)"', html)
        if not resource_match or not file_match:
            raise LiveDataUnavailable(
                "The selected district's data.gov.in page has no consumable Census CSV resource."
            )
        resource_id = resource_match.group(1)
        try:
            file_url = json.loads('"' + file_match.group(1) + '"')
        except json.JSONDecodeError as exc:
            raise LiveDataUnavailable("The Census resource URL could not be decoded.") from exc
        parsed_file = urlsplit(file_url)
        if (
            parsed_file.scheme != "https"
            or parsed_file.hostname != "censusindia.gov.in"
            or not parsed_file.path.startswith("/datagov/TDVD_Files/")
            or not parsed_file.path.endswith(".csv")
        ):
            raise LiveDataUnavailable("The district resource does not point to the reviewed Census CSV host.")

        try:
            csv_bytes = _fetch_public_bytes(
                file_url, accept="text/csv,application/csv", maximum_bytes=MAX_CENSUS_CSV_BYTES
            )
            local_cache_note = None
        except LiveDataUnavailable:
            local_file = _local_census_cache_file(file_url)
            if local_file is None:
                raise
            csv_bytes = local_file.read_bytes()
            if len(csv_bytes) > MAX_CENSUS_CSV_BYTES:
                raise LiveDataUnavailable("The local official Census district file exceeds the safety limit.")
            local_cache_note = f"Live retrieval was unavailable; used the local cache of the exact official file {local_file.name}."
        csv_content = csv_bytes.decode("utf-8-sig", errors="strict")
        reader = csv.DictReader(io.StringIO(csv_content))
        required_fields = {
            "State Name",
            "District Name",
            "CD Block Name",
            "Total  Households ",
            "Total Population of Village",
        }
        if not reader.fieldnames or not required_fields.issubset(reader.fieldnames):
            raise LiveDataUnavailable("The official Census CSV does not contain the required CD-block fields.")
        records = tuple(dict(row) for row in reader)
        if not records:
            raise LiveDataUnavailable("The official Census district CSV contains no village records.")
        entry = _CensusDistrictCacheEntry(
            records=records,
            resource_id=resource_id,
            resource_url=resource_url,
            retrieved_at=datetime.now(timezone.utc),
            expires_at=monotonic() + self._cache_ttl_seconds(),
            retrieval_note=local_cache_note,
        )
        with _CENSUS_DISTRICT_CACHE_LOCK:
            _CENSUS_DISTRICT_CACHE[key] = entry
        return entry

    def block_options(self, state_name: str, district_name: str) -> tuple[list[IndiaAdministrativeOption], _CensusDistrictCacheEntry]:
        """Return official Census CD-block names from a selected district file."""
        lookup = type("CensusLookup", (), {"state_name": state_name, "district_name": district_name})()
        entry = self._district_records(lookup)  # type: ignore[arg-type]
        names = {
            " ".join(str(row.get("CD Block Name", "")).split())
            for row in entry.records
            if str(row.get("CD Block Name", "")).strip()
        }
        options = [
            IndiaAdministrativeOption(
                id=f"census-block:{_normalise_geography(name)}",
                name=name,
                admin_level="census-cd-block",
            )
            for name in sorted(names, key=str.casefold)
        ]
        if not options:
            raise LiveDataUnavailable("The official Census district file contains no CD-block names.")
        return options, entry

    @staticmethod
    def _non_negative_number(value: object, field_name: str) -> int:
        if value is None or not str(value).strip() or _normalise_text(value) in {"na", "n a"}:
            return 0
        parsed = _to_int(value, field_name)
        return parsed if parsed is not None else 0

    def fetch(self, request: CompetitorMappingRequest) -> DemographicSnapshot:
        district = self._district_records(request)
        state_key = _normalise_geography(request.state_name)
        state_key = self._state_data_aliases.get(state_key, state_key)
        district_key = _normalise_district(request.district_name)
        block_key = _normalise_block(request.block_name)
        matches = [
            row
            for row in district.records
            if _normalise_geography(row.get("State Name", "")) == state_key
            and _normalise_district(row.get("District Name", "")) == district_key
            and _normalise_block(row.get("CD Block Name", "")) == block_key
        ]
        if not matches:
            raise LiveDataUnavailable(
                "The official Census district resource has no exact CD-block match for the selected block name."
            )
        total_population = sum(
            self._non_negative_number(row.get("Total Population of Village"), "village population")
            for row in matches
        )
        households = sum(
            self._non_negative_number(row.get("Total  Households "), "village households")
            for row in matches
        )
        if total_population <= 0:
            raise LiveDataUnavailable("The matched Census village rows have no positive population total.")
        return DemographicSnapshot(
            total_population=total_population,
            households=households or None,
            working_population=None,
            segments={},
            source_name=CENSUS_SOURCE_NAME,
            source_url=district.resource_url,
            source_id=district.resource_id,
            source_notes=(
                f"Exact data.gov.in resource {district.resource_id}; summed {len(matches)} rural village rows "
                f"for CD Block {request.block_name}. Census reference year 2011."
                + (f" {district.retrieval_note}" if district.retrieval_note else "")
            ),
        )


class OverpassClient:
    def __init__(self) -> None:
        configured_url = os.getenv("VYAPARSATHI_OVERPASS_URL")
        self.urls = [
            _configured_https_url("VYAPARSATHI_OVERPASS_URL", DEFAULT_OVERPASS_URL)
        ]
        if not configured_url or configured_url == DEFAULT_OVERPASS_URL:
            self.urls.append(
                _configured_https_url("VYAPARSATHI_OVERPASS_FALLBACK_URL", SECONDARY_OVERPASS_URL)
            )

    def query(self, query: str, *, timeout_seconds: Optional[float] = None) -> list[dict[str, Any]]:
        last_error: Optional[LiveDataUnavailable] = None
        for url in self.urls:
            try:
                payload = _fetch_json(url, payload=query, timeout_seconds=timeout_seconds)
                if isinstance(payload, dict) and payload.get('remark'):
                    raise LiveDataUnavailable('OpenStreetMap could not complete its query; incomplete records were discarded.')
                elements = payload.get("elements") if isinstance(payload, dict) else None
                if not isinstance(elements, list):
                    raise LiveDataUnavailable("OpenStreetMap returned an unexpected response.")
                return [element for element in elements if isinstance(element, dict)]
            except LiveDataUnavailable as exc:
                last_error = exc
        raise last_error or LiveDataUnavailable("OpenStreetMap could not be reached.")

    @staticmethod
    def _feature_query_timeout() -> float:
        try:
            value = float(os.getenv("VYAPARSATHI_OSM_FEATURE_TIMEOUT_SECONDS", "20"))
        except ValueError as exc:
            raise LiveDataUnavailable("VYAPARSATHI_OSM_FEATURE_TIMEOUT_SECONDS must be a number.") from exc
        if value <= 0:
            raise LiveDataUnavailable("VYAPARSATHI_OSM_FEATURE_TIMEOUT_SECONDS must be positive.")
        return value

    def resolve_block(
        self, latitude: float, longitude: float, block_name: str, district_osm_id: Optional[str] = None
    ) -> BlockBoundary:
        admin_level_pattern = _block_admin_level_pattern()
        if district_osm_id:
            district_area_id = _area_id_from_reference(district_osm_id)
            query = f"""[out:json][timeout:30];
area({district_area_id})->.district;
relation(area.district)["boundary"="administrative"]["admin_level"~"{admin_level_pattern}"]["name"="{_ql_string(block_name)}"];
out tags;"""
        else:
            query = f"""[out:json][timeout:30];
is_in({latitude},{longitude})->.containing;
area.containing["boundary"="administrative"]["admin_level"~"{admin_level_pattern}"]["name"="{_ql_string(block_name)}"];
out tags;"""
        matches = self.query(query, timeout_seconds=self._feature_query_timeout())
        if len(matches) != 1:
            raise LiveDataUnavailable(
                "OpenStreetMap could not verify one administrative block with that name at the selected coordinates."
            )
        element = matches[0]
        try:
            area_id = int(element["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LiveDataUnavailable("OpenStreetMap returned an invalid administrative-area identifier.") from exc
        tags = element.get("tags") if isinstance(element.get("tags"), dict) else {}
        return BlockBoundary(
            osm_area_id=area_id,
            name=str(tags.get("name", block_name)),
            admin_level=str(tags["admin_level"]) if tags.get("admin_level") else None,
        )

    def resolve_block_by_names(
        self, state_name: str, district_name: str, block_name: str
    ) -> tuple[BlockBoundary, float, float, str]:
        """Resolve a block and center when the offline LGD row has no geometry."""
        block_levels = _block_admin_level_pattern()
        query = f"""[out:json][timeout:30];
area["boundary"="administrative"]["admin_level"="4"]["name"="{_ql_string(state_name)}"]->.state;
area["boundary"="administrative"]["admin_level"="5"]["name"="{_ql_string(district_name)}"](area.state)->.district;
relation(area.district)["boundary"="administrative"]["admin_level"~"{block_levels}"];
out center tags;"""
        elements = self.query(query, timeout_seconds=self._feature_query_timeout())
        requested = _normalise_geography(block_name)
        matches = []
        for element in elements:
            tags = element.get("tags") if isinstance(element.get("tags"), dict) else {}
            center = element.get("center") if isinstance(element.get("center"), dict) else {}
            if _normalise_geography(tags.get("name", "")) != requested:
                continue
            if element.get("id") is None or center.get("lat") is None or center.get("lon") is None:
                continue
            matches.append((element, center, tags))
        if len(matches) != 1:
            raise LiveDataUnavailable(
                "OpenStreetMap could not verify one administrative block with the selected LGD name."
            )
        element, center, tags = matches[0]
        block_id = int(element["id"])
        return (
            BlockBoundary(
                osm_area_id=3_600_000_000 + block_id,
                name=str(tags.get("name", block_name)),
                admin_level=str(tags.get("admin_level", "")) or None,
            ),
            float(center["lat"]),
            float(center["lon"]),
            f"relation:{block_id}",
        )

    def mapped_competitors(
        self, block: BlockBoundary, osm_tags: Iterable[dict[str, str]]
    ) -> list[dict[str, Any]]:
        clauses = []
        for tag in osm_tags:
            if len(tag) != 1:
                continue
            key, value = next(iter(tag.items()))
            clauses.append(f'nwr(area.block)["{_ql_string(key)}"="{_ql_string(value)}"];')
        if not clauses:
            raise LiveDataUnavailable("The selected business category has no live OpenStreetMap mapping rules.")
        joined_clauses = " ".join(clauses)
        query = f"""[out:json][timeout:60];
area({block.osm_area_id})->.block;
(
  {joined_clauses}
);
out center tags;"""
        return self.query(query, timeout_seconds=self._feature_query_timeout())

    def commercial_features(self, block: BlockBoundary) -> list[dict[str, Any]]:
        query = f"""[out:json][timeout:60];
area({block.osm_area_id})->.block;
(
  nwr(area.block)["shop"];
  nwr(area.block)["office"];
  nwr(area.block)["amenity"="bank"];
  nwr(area.block)["amenity"="marketplace"];
  nwr(area.block)["landuse"="commercial"];
);
out ids;"""
        return self.query(query, timeout_seconds=self._feature_query_timeout())

    def administrative_options(
        self, level: str, parent_id: Optional[str] = None
    ) -> list[IndiaAdministrativeOption]:
        timeout_seconds = float(os.getenv("VYAPARSATHI_ADMIN_DATA_TIMEOUT_SECONDS", "5"))
        if level == "state":
            query = """[out:json][timeout:5];
relation["boundary"="administrative"]["admin_level"="4"]["ISO3166-2"~"^IN-"];
out center tags;"""
        else:
            if not parent_id:
                raise LiveDataUnavailable("A parent administrative area is required.")
            level_filter = "5" if level == "district" else _block_admin_level_pattern()
            if level == "district" and parent_id.startswith("state:"):
                state_name = _INDIA_STATE_NAMES.get(parent_id.removeprefix("state:"))
                if not state_name:
                    raise LiveDataUnavailable("The selected State/UT identifier is invalid.")
                query = f"""[out:json][timeout:5];
area["boundary"="administrative"]["admin_level"="4"]["name"="{_ql_string(state_name)}"]->.parent;
relation(area.parent)["boundary"="administrative"]["admin_level"="5"];
out center tags;"""
            else:
                parent_area_id = _area_id_from_reference(parent_id)
                query = f"""[out:json][timeout:5];
area({parent_area_id})->.parent;
relation(area.parent)["boundary"="administrative"]["admin_level"~"{level_filter if level == "block" else "^(" + level_filter + ")$"}"];
out center tags;"""
        elements = self.query(query, timeout_seconds=timeout_seconds)
        options: list[IndiaAdministrativeOption] = []
        for element in elements:
            tags = element.get("tags") if isinstance(element.get("tags"), dict) else {}
            name = tags.get("name")
            if not name or element.get("type") != "relation" or element.get("id") is None:
                continue
            center = element.get("center") if isinstance(element.get("center"), dict) else {}
            latitude = center.get("lat")
            longitude = center.get("lon")
            options.append(
                IndiaAdministrativeOption(
                    id=f"relation:{element['id']}",
                    name=str(name),
                    admin_level=str(tags.get("admin_level", "")),
                    latitude=float(latitude) if latitude is not None else None,
                    longitude=float(longitude) if longitude is not None else None,
                )
            )
        unique = {option.id: option for option in options}
        return sorted(unique.values(), key=lambda option: option.name.casefold())


def _unique_elements(elements: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for element in elements:
        element_type = str(element.get("type", ""))
        element_id = str(element.get("id", ""))
        if element_type and element_id:
            unique[(element_type, element_id)] = element
    return list(unique.values())


def _mapped_competitor(element: dict[str, Any], allowed_tags: set[str]) -> MappedCompetitor:
    tags = element.get("tags") if isinstance(element.get("tags"), dict) else {}
    center = element.get("center") if isinstance(element.get("center"), dict) else {}
    latitude = element.get("lat", center.get("lat"))
    longitude = element.get("lon", center.get("lon"))
    visible_tags = {
        key: str(value)
        for key, value in tags.items()
        if key in allowed_tags or key in {"name", "brand"}
    }
    return MappedCompetitor(
        osm_id=str(element["id"]),
        osm_type=str(element["type"]),
        name=str(tags["name"]) if tags.get("name") else None,
        latitude=float(latitude) if latitude is not None else None,
        longitude=float(longitude) if longitude is not None else None,
        tags=visible_tags,
    )


def _weighted_target_population(category: BusinessCategory, demographics: DemographicSnapshot) -> Optional[float]:
    if not category.target_segments:
        return None
    values: list[tuple[int, float]] = []
    for segment in category.target_segments:
        population = demographics.segments.get(segment.segment)
        if population is None:
            return None
        values.append((population, segment.weight))
    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0:
        return None
    return round(sum(population * weight for population, weight in values) / total_weight, 2)


def _insufficient_response(
    request: CompetitorMappingRequest,
    message: str,
    provenance: Optional[list[DataProvenance]] = None,
    demographics: Optional[DemographicMappingContext] = None,
    methodology: Optional[list[str]] = None,
) -> CompetitorMappingResponse:
    return CompetitorMappingResponse(
        status="INSUFFICIENT",
        block_name=request.block_name,
        category_id=request.category_id,
        confidence=ConfidenceLevel.LOW,
        demographics=demographics,
        methodology=methodology or [],
        limitations=[message, "No seeded or synthetic data was used for this result."],
        data_provenance=provenance or [],
    )


def analyze_live_competitor_mapping(request: CompetitorMappingRequest) -> CompetitorMappingResponse:
    """Return a block-level competitor density from live public-source records only."""

    category = _load_category(request.category_id)
    if category is None:
        return _insufficient_response(request, "Business category not found.")
    if not category.osm_competitor_tags:
        return _insufficient_response(
            request, "The selected business category has no configured OpenStreetMap competitor tags."
        )

    try:
        demographics = PublicDemographicsApi().fetch(request)
    except LiveDataUnavailable as exc:
        return _insufficient_response(request, str(exc))

    demographic_provenance = DataProvenance(
        source_id=demographics.source_id,
        source_name=demographics.source_name,
        source_url=demographics.source_url,
        data_type=DataClassification.VERIFIED,
        last_verified=datetime.now(timezone.utc),
        confidence=ConfidenceLevel.HIGH,
        notes=demographics.source_notes
        or "Official public records matched exactly to the requested state, district, and block.",
    )


    provenance = [demographic_provenance]

    try:
        overpass = OverpassClient()
        if request.district_osm_id:
            block = overpass.resolve_block(
                request.latitude, request.longitude, request.block_name, request.district_osm_id
            )
        else:
            block = overpass.resolve_block(request.latitude, request.longitude, request.block_name)
        with ThreadPoolExecutor(max_workers=2) as pool:
            competitor_future = pool.submit(
                overpass.mapped_competitors, block, category.osm_competitor_tags
            )
            commercial_future = pool.submit(overpass.commercial_features, block)
            competitor_elements = _unique_elements(competitor_future.result())
            commercial_elements = _unique_elements(commercial_future.result())
    except LiveDataUnavailable as exc:
        demographic_context = DemographicMappingContext(
            total_population=demographics.total_population,
            households=demographics.households,
            working_population=demographics.working_population,
            weighted_target_population_proxy=_weighted_target_population(category, demographics),
        )
        return _insufficient_response(
            request,
            str(exc),
            provenance,
            demographic_context,
            [
                "The Census of India 2011 Village Amenities file was matched exactly to the selected state, district, and CD block.",
                "Mapped-business counts are withheld because OpenStreetMap could not verify a boundary for this Census CD block.",
            ],
        )

    provenance.append(_osm_provenance())
    target_population = _weighted_target_population(category, demographics)
    competitor_count = len(competitor_elements)
    commercial_count = len(commercial_elements)
    per_1000_residents = round(competitor_count * 1000 / demographics.total_population, 4)
    per_1000_target_customers = (
        round(competitor_count * 1000 / target_population, 4) if target_population else None
    )
    commercial_per_1000 = round(commercial_count * 1000 / demographics.total_population, 4)
    per_100_commercial = round(competitor_count * 100 / commercial_count, 4) if commercial_count else None
    allowed_tag_keys = {key for tag in category.osm_competitor_tags for key in tag}
    mapped_competitors = [
        _mapped_competitor(element, allowed_tag_keys)
        for element in sorted(competitor_elements, key=lambda item: str(item.get("id")))[:MAX_RETURNED_COMPETITORS]
    ]
    limitations = [
        "OpenStreetMap contains mapped businesses and commercial features, not a complete census of formal or informal businesses.",
        "Density is normalized from observed public records; it is not an estimate of unrecorded businesses.",
        "The demographic denominator is Census 2011 rural village population aggregated by CD block; it excludes statutory-town residents and may not match current boundaries.",
        "data.gov.in does not expose a row API for this Census catalog; the exact district resource UUID and directly hosted Census CSV are verified for each result.",
    ]
    if target_population is None:
        limitations.append(
            "The public demographics record lacks one or more category target-segment fields, so target-customer density is unavailable."
        )
    if competitor_count > MAX_RETURNED_COMPETITORS:
        limitations.append(
            f"Only the first {MAX_RETURNED_COMPETITORS} mapped competitors are returned, while the count covers all mapped results."
        )

    return CompetitorMappingResponse(
        status="AVAILABLE",
        block_id=str(block.osm_area_id),
        block_name=block.name,
        block_admin_level=block.admin_level,
        category_id=request.category_id,
        mapped_competitor_count=competitor_count,
        mapped_competitors=mapped_competitors,
        competitors_per_1000_residents=per_1000_residents,
        competitors_per_1000_target_customers=per_1000_target_customers,
        demographics=DemographicMappingContext(
            total_population=demographics.total_population,
            households=demographics.households,
            working_population=demographics.working_population,
            weighted_target_population_proxy=target_population,
        ),
        economic_context=EconomicMappingContext(
            mapped_commercial_features=commercial_count,
            commercial_features_per_1000_residents=commercial_per_1000,
            competitors_per_100_commercial_features=per_100_commercial,
        ),
        confidence=ConfidenceLevel.MEDIUM,
        methodology=[
            "OpenStreetMap verifies the requested administrative block at the submitted coordinate.",
            "OpenStreetMap business tags configured for the selected category are counted within that block.",
            "Competitor counts are normalized using the matching public block-demographics record and observed commercial activity.",
        ],
        limitations=limitations,
        data_provenance=provenance,
    )


def resolve_administrative_location(
    state_name: str, district_name: str, block_name: str
):
    """Resolve live OSM geometry for an offline LGD selection."""
    from app.schemas.market import AdministrativeLocationResponse

    try:
        _block, latitude, longitude, block_id = OverpassClient().resolve_block_by_names(
            state_name, district_name, block_name
        )
        return AdministrativeLocationResponse(
            status="AVAILABLE", latitude=latitude, longitude=longitude,
            block_osm_id=block_id, limitations=[
                "Administrative geometry was resolved from the live OpenStreetMap record only when analysis was requested."
            ], data_provenance=[_osm_provenance()],
        )
    except LiveDataUnavailable as exc:
        return AdministrativeLocationResponse(
            status="INSUFFICIENT", limitations=[str(exc), "No coordinates were inferred from the LGD code."],
            data_provenance=[_osm_provenance()],
        )


def get_india_administrative_options(
    level: str,
    parent_id: Optional[str] = None,
    state_name: Optional[str] = None,
    district_name: Optional[str] = None,
) -> IndiaAdministrativeOptionsResponse:
    """Load one level of India's live administrative hierarchy from Overpass."""

    if level not in {"state", "district", "block"}:
        return IndiaAdministrativeOptionsResponse(
            status="INSUFFICIENT",
            level="state",
            parent_id=parent_id,
            confidence=ConfidenceLevel.LOW,
            limitations=["The requested administrative level is unsupported."],
        )
    if level == "state" and parent_id:
        return IndiaAdministrativeOptionsResponse(
            status="INSUFFICIENT",
            level=level,
            parent_id=parent_id,
            confidence=ConfidenceLevel.LOW,
            limitations=["States do not accept a parent administrative area."],
        )
    if level != "state" and not parent_id:
        return IndiaAdministrativeOptionsResponse(
            status="INSUFFICIENT",
            level=level,
            parent_id=parent_id,
            confidence=ConfidenceLevel.LOW,
            limitations=["Select the parent administrative area first."],
        )

    # Imported Ministry of Panchayati Raj LGD records are the primary source
    # for dropdown navigation. They are local, verified, and avoid any public
    # network dependency during a user's State → District → Block selection.
    from app.services.market.offline_administrative_index import lookup as offline_lookup
    offline_result = offline_lookup(level, parent_id)
    if offline_result is not None:
        return offline_result

    # Blocks are names from the official Census district file when available.
    # This avoids a slow boundary scan just to fill the final selector.
    if level == "block" and state_name and district_name:
        try:
            census_options, census_entry = PublicDemographicsApi().block_options(state_name, district_name)
            return IndiaAdministrativeOptionsResponse(
                status="AVAILABLE", level="block", parent_id=parent_id, options=census_options,
                confidence=ConfidenceLevel.HIGH,
                limitations=[
                    "CD-block names are from the exact official Census district file; the source does not publish block boundary geometry.",
                    "Mapped-business counts are shown only if OpenStreetMap can separately verify the selected block boundary.",
                ],
                data_provenance=[DataProvenance(
                    source_id=census_entry.resource_id, source_name=CENSUS_SOURCE_NAME,
                    source_url=census_entry.resource_url, data_type=DataClassification.VERIFIED,
                    last_verified=census_entry.retrieved_at, confidence=ConfidenceLevel.HIGH,
                    notes="Official Census 2011 Village Amenities CSV; CD-block names only.",
                )],
            )
        except LiveDataUnavailable:
            # No local/downloaded Census row: try the live OSM boundary list below.
            pass

    cache_entry = _cached_administrative_options(level, parent_id)
    cache_hit = cache_entry is not None
    if cache_entry is None:
        try:
            options = OverpassClient().administrative_options(level, parent_id)
            if options:
                cache_entry = _cache_administrative_options(level, parent_id, options)
        except LiveDataUnavailable as exc:
            if level == "block" and state_name and district_name:
                options = []
            else:
                return IndiaAdministrativeOptionsResponse(
                    status="INSUFFICIENT",
                    level=level,
                    parent_id=parent_id,
                    confidence=ConfidenceLevel.LOW,
                    limitations=[str(exc), "No seeded or synthetic administrative options were used."],
                )

    options = list(cache_entry.options) if cache_entry else []

    if level == "block" and not options and state_name and district_name:
        try:
            census_options, census_entry = PublicDemographicsApi().block_options(state_name, district_name)
            return IndiaAdministrativeOptionsResponse(
                status="AVAILABLE",
                level="block",
                parent_id=parent_id,
                options=census_options,
                confidence=ConfidenceLevel.HIGH,
                limitations=[
                    "CD-block names are from the exact official Census district file; the source does not publish block boundary geometry.",
                    "Mapped-business counts are shown only if OpenStreetMap can separately verify the selected block boundary.",
                ],
                data_provenance=[
                    DataProvenance(
                        source_id=census_entry.resource_id,
                        source_name=CENSUS_SOURCE_NAME,
                        source_url=census_entry.resource_url,
                        data_type=DataClassification.VERIFIED,
                        last_verified=census_entry.retrieved_at,
                        confidence=ConfidenceLevel.HIGH,
                        notes="Official Census 2011 Village Amenities CSV; CD-block names only.",
                    )
                ],
            )
        except LiveDataUnavailable as exc:
            return IndiaAdministrativeOptionsResponse(
                status="INSUFFICIENT",
                level="block",
                parent_id=parent_id,
                confidence=ConfidenceLevel.LOW,
                limitations=[str(exc), "No seeded or synthetic administrative options were used."],
                data_provenance=[_osm_provenance()],
            )

    if not options:
        return IndiaAdministrativeOptionsResponse(
            status="INSUFFICIENT",
            level=level,
            parent_id=parent_id,
            confidence=ConfidenceLevel.LOW,
            limitations=["The public source returned no administrative options for this selection."],
            data_provenance=[_osm_provenance()],
        )

    limitations = [
        "Administrative names and centers are live OpenStreetMap records.",
        "Coverage and naming may vary by contributor and area.",
    ]
    if cache_hit:
        limitations.append(
            "A recently retrieved live administrative response was served from the application cache for faster navigation."
        )

    return IndiaAdministrativeOptionsResponse(
        status="AVAILABLE",
        level=level,
        parent_id=parent_id,
        options=options,
        confidence=ConfidenceLevel.MEDIUM,
        limitations=limitations,
        data_provenance=[_osm_provenance(cache_entry.retrieved_at if cache_entry else None)],
    )
