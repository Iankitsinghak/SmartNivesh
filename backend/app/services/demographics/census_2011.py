"""Low-latency access to the imported Census of India 2011 PCA workbook."""

from __future__ import annotations

import os
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

from app.core.enums import ConfidenceLevel, DataClassification
from app.schemas.common import DataProvenance
from app.schemas.market import IndiaAdministrativeOption, IndiaAdministrativeOptionsResponse
from app.schemas.market import LocalDemographicsResponse


SOURCE_URL = "https://censusindia.gov.in/nada/index.php/catalog/42559"
SOURCE_NAME = "Census of India 2011 Primary Census Abstract"

# The local-government hierarchy uses current district names, while the supplied
# Census workbook uses the 2011 names.  These aliases only bridge a known rename
# or split predecessor; the requested sub-district must still match before a
# Census record can be returned.
_LEGACY_DISTRICT_KEYS = {
    "cooch behar": "koch bihar",
    "howrah": "haora",
    "hooghly": "hugli",
    "malda": "maldah",
    "purulia": "puruliya",
    "north 24 parganas": "north twenty four parganas",
    "south 24 parganas": "south twenty four parganas",
    "purba bardhaman": "barddhaman",
    "paschim bardhaman": "barddhaman",
    "jhargram": "paschim medinipur",
    "kalimpong": "darjiling",
    "alipurduar": "jalpaiguri",
}


def _database_path() -> Path:
    configured = os.getenv("VYAPARSATHI_CENSUS_2011_DB")
    return Path(configured) if configured else Path(__file__).resolve().parents[3] / "data" / "census_2011.sqlite"


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def available() -> bool:
    return _database_path().is_file()


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{_database_path()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _provenance() -> DataProvenance:
    return DataProvenance(
        source_id="CENSUS_2011_PCA_LOCAL",
        source_name=SOURCE_NAME,
        source_url=SOURCE_URL,
        data_type=DataClassification.VERIFIED,
        last_verified=datetime.now(timezone.utc),
        confidence=ConfidenceLevel.HIGH,
        notes="Imported locally from the supplied 2011 India State/District/Sub-district/Village PCA workbook.",
    )


def _consonants(value: str) -> str:
    return "".join(character for character in value if character not in "aeiou")


def _resolve_key(db: sqlite3.Connection, column: str, value: object, where: str, parameters: tuple[object, ...]) -> Optional[str]:
    requested = normalize(value)
    if not requested:
        return None
    rows = db.execute(
        f"SELECT DISTINCT {column} FROM census_geo WHERE {where} AND {column} IS NOT NULL",
        parameters,
    ).fetchall()
    candidates = [str(row[0]) for row in rows]
    if requested in candidates:
        return requested
    legacy_key = _LEGACY_DISTRICT_KEYS.get(requested) if column == "district_key" else None
    if legacy_key in candidates:
        return legacy_key
    if not candidates:
        return None

    def score(candidate: str) -> float:
        direct = SequenceMatcher(None, requested, candidate).ratio()
        phonetic = SequenceMatcher(None, _consonants(requested), _consonants(candidate)).ratio()
        return max(direct, phonetic)

    ranked = sorted(((score(candidate), candidate) for candidate in candidates), reverse=True)
    best_score, best_candidate = ranked[0]
    second_score = ranked[1][0] if len(ranked) > 1 else 0.0
    if best_score >= 0.72 and best_score - second_score >= 0.08:
        return best_candidate
    return None


def administrative_options(
    level: str, parent_id: Optional[str], state_name: Optional[str], district_name: Optional[str]
) -> Optional[IndiaAdministrativeOptionsResponse]:
    """Return Census district or sub-district choices without a network call."""
    if not available() or level not in {"district", "block"}:
        return None
    with _connection() as db:
        state_key = _resolve_key(db, "state_key", state_name, "1=1", ())
        district_key = _resolve_key(db, "district_key", district_name, "state_key=?", (state_key,)) if state_key else None
        if not state_key or (level == "block" and not district_key):
            return None
        if level == "district":
            rows = db.execute(
                "SELECT state_code, district_code, name FROM census_geo "
                "WHERE level='DISTRICT' AND tru='Total' AND state_key=? ORDER BY name COLLATE NOCASE",
                (state_key,),
            ).fetchall()
            options = [IndiaAdministrativeOption(id=f"census-district:{row['state_code']}:{row['district_code']}", name=row["name"], admin_level="census-district") for row in rows]
        else:
            rows = db.execute(
                "SELECT state_code, district_code, subdistrict_code, name FROM census_geo "
                "WHERE level='SUB-DISTRICT' AND tru='Total' AND state_key=? AND district_key=? ORDER BY name COLLATE NOCASE",
                (state_key, district_key),
            ).fetchall()
            options = [IndiaAdministrativeOption(id=f"census-subdistrict:{row['state_code']}:{row['district_code']}:{row['subdistrict_code']}", name=row["name"], admin_level="census-sub-district") for row in rows]
    if not options:
        return None
    label = "districts" if level == "district" else "sub-districts"
    return IndiaAdministrativeOptionsResponse(
        status="AVAILABLE", level=level, parent_id=parent_id, options=options,
        confidence=ConfidenceLevel.HIGH,
        limitations=[f"Loaded locally from the supplied Census 2011 PCA workbook. These are Census 2011 {label}; current administrative boundaries may differ."],
        data_provenance=[_provenance()],
    )


@dataclass(frozen=True)
class CensusSnapshot:
    total_population: int
    households: Optional[int]
    working_population: Optional[int]
    segments: dict[str, int]
    source_name: str = SOURCE_NAME
    source_url: str = SOURCE_URL
    source_id: str = "CENSUS_2011_PCA_LOCAL"
    source_notes: str = "Local Census 2011 PCA record selected by exact normalized state, district, and sub-district name."


def subdistrict_snapshot(state_name: str, district_name: str, subdistrict_name: str) -> Optional[CensusSnapshot]:
    """Return the rural sub-district row, falling back to the total row if rural is absent."""
    if not available():
        return None
    with _connection() as db:
        state_key = _resolve_key(db, "state_key", state_name, "1=1", ())
        district_key = _resolve_key(db, "district_key", district_name, "state_key=?", (state_key,)) if state_key else None
        subdistrict_key = (
            _resolve_key(db, "name_key", subdistrict_name, "level='SUB-DISTRICT' AND state_key=? AND district_key=?", (state_key, district_key))
            if state_key and district_key else None
        )
        if not state_key or not district_key or not subdistrict_key:
            return None
        row = db.execute(
            "SELECT * FROM census_geo WHERE level='SUB-DISTRICT' AND state_key=? AND district_key=? AND name_key=? "
            "ORDER BY CASE tru WHEN 'Rural' THEN 0 WHEN 'Total' THEN 1 ELSE 2 END LIMIT 1",
            (state_key, district_key, subdistrict_key),
        ).fetchone()
    if row is None or row["total_population"] is None or row["total_population"] <= 0:
        return None
    return CensusSnapshot(
        total_population=int(row["total_population"]), households=int(row["households"]) if row["households"] is not None else None,
        working_population=int(row["working_population"]) if row["working_population"] is not None else None,
        segments={"age_0_6": int(row["population_0_6"] or 0), "working_population": int(row["working_population"] or 0)},
        source_notes=(f"Local Census 2011 PCA {row['tru']} row for sub-district {row['name']}; "
                      f"state code {row['state_code']}, district code {row['district_code']}, sub-district code {row['subdistrict_code']}.")
    )


def local_demographics(state_name: str, district_name: str, subdistrict_name: str) -> LocalDemographicsResponse:
    snapshot = subdistrict_snapshot(state_name, district_name, subdistrict_name)
    if snapshot is None:
        return LocalDemographicsResponse(
            status="INSUFFICIENT",
            limitations=["No exact Census 2011 sub-district record matched this State, District, and Sub-district selection."],
        )
    return LocalDemographicsResponse(
        status="AVAILABLE",
        total_population=snapshot.total_population,
        households=snapshot.households,
        working_population=snapshot.working_population,
        population_0_6=snapshot.segments.get("age_0_6"),
        limitations=[
            "This is a Census 2011 sub-district record. It is not a current population estimate or a 5 km/10 km radius population calculation.",
        ],
        data_provenance=[_provenance()],
    )
