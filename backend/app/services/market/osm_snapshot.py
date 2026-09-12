"""Low-latency reads from a locally indexed OpenStreetMap POI snapshot."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Iterable

from app.utils.geo import haversine_km


def database_path() -> Path:
    configured = os.getenv("VYAPARSATHI_OSM_COMPETITORS_DB")
    return Path(configured) if configured else Path(__file__).resolve().parents[3] / "data" / "osm_competitors.sqlite"


def available() -> bool:
    return database_path().is_file()


def nearby_points(latitude: float, longitude: float, allowed_tags: Iterable[dict[str, str]], radius_km: float = 10) -> list[dict[str, object]]:
    """Return matching, coordinate-bearing OSM POIs within a geodesic radius.

    The RTree is only a fast bounding-box prefilter. Final inclusion always uses
    haversine distance so the API's 2/5/10 km bands remain geographically correct.
    """
    if not available():
        return []
    # One degree latitude is roughly 111 km. Longitude varies by latitude.
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / max(111.0 * abs(__import__("math").cos(__import__("math").radians(latitude))), 0.1)
    rules = tuple((str(key), str(value)) for rule in allowed_tags for key, value in rule.items())
    if not rules:
        return []
    connection = sqlite3.connect(f"file:{database_path()}?mode=ro", uri=True, timeout=1)
    try:
        try:
            rows = connection.execute(
                "SELECT poi.osm_type, poi.osm_id, poi.name, poi.latitude, poi.longitude, poi.tags "
                "FROM poi_rtree AS box JOIN osm_poi AS poi ON poi.rowid = box.id "
                "WHERE box.min_lat <= ? AND box.max_lat >= ? AND box.min_lon <= ? AND box.max_lon >= ?",
                (latitude + lat_delta, latitude - lat_delta, longitude + lon_delta, longitude - lon_delta),
            ).fetchall()
        except sqlite3.OperationalError:
            # During a one-time snapshot build, live provider evidence remains
            # available instead of exposing a database-lock error to the user.
            return []
    finally:
        connection.close()
    found: list[dict[str, object]] = []
    for osm_type, osm_id, name, lat, lon, serialized_tags in rows:
        try:
            tags = json.loads(serialized_tags)
        except json.JSONDecodeError:
            continue
        if not any(tags.get(key) == value for key, value in rules):
            continue
        distance = haversine_km(latitude, longitude, float(lat), float(lon))
        if distance <= radius_km:
            found.append({
                "osm_type": osm_type, "osm_id": str(osm_id), "name": name,
                "latitude": float(lat), "longitude": float(lon), "tags": tags,
                "distance_km": distance,
            })
    return sorted(found, key=lambda item: float(item["distance_km"]))
