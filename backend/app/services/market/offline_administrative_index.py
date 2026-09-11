"""Read-only access to imported official LGD administrative records."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.core.enums import ConfidenceLevel, DataClassification
from app.schemas.common import DataProvenance
from app.schemas.market import IndiaAdministrativeOption, IndiaAdministrativeOptionsResponse


@lru_cache(maxsize=1)
def _index() -> dict:
    path = Path(__file__).resolve().parents[3] / "data" / "lgd_administrative_index.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def clear_offline_administrative_index_cache() -> None:
    _index.cache_clear()


def lookup(level: str, parent_id: Optional[str]) -> Optional[IndiaAdministrativeOptionsResponse]:
    data = _index()
    source = data.get("source") if isinstance(data.get("source"), dict) else None
    if not source or level not in {"district", "block"} or not parent_id:
        return None
    records = data.get("districts", []) if level == "district" else data.get("blocks", [])
    parent_key = "state_id" if level == "district" else "district_id"
    matches = [record for record in records if record.get(parent_key) == parent_id]
    if not matches:
        return None
    options = [
        IndiaAdministrativeOption(
            id=str(record["id"]), name=str(record["name"]),
            admin_level="lgd-district" if level == "district" else "lgd-development-block",
        )
        for record in sorted(matches, key=lambda item: str(item["name"]).casefold())
    ]
    generated = data.get("generated_at")
    try:
        verified_at = datetime.fromisoformat(str(generated).replace("Z", "+00:00"))
    except ValueError:
        verified_at = datetime.now(timezone.utc)
    return IndiaAdministrativeOptionsResponse(
        status="AVAILABLE", level=level, parent_id=parent_id, options=options,
        confidence=ConfidenceLevel.HIGH,
        limitations=[
            "Loaded instantly from the bundled official LGD export.",
            "LGD directory records provide administrative names and codes, not boundary geometry.",
        ],
        data_provenance=[DataProvenance(
            source_id=f"LGD_OFFLINE_{source.get('state_lgd_code', 'IMPORT')}",
            source_name=str(source.get("name", "Local Government Directory (LGD)")),
            source_url=str(source.get("url", "https://lgdirectory.gov.in/")),
            data_type=DataClassification.VERIFIED, last_verified=verified_at,
            confidence=ConfidenceLevel.HIGH,
            notes=f"Bundled from {source.get('archive_name', 'official LGD export')}; State/UT: {source.get('state_name', 'not recorded')}.",
        )],
    )
