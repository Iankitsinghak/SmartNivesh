"""Create VyaparSathi's compact nearby-business index from an OSM PBF extract.

Usage:
    python scripts/index_osm_competitors.py /absolute/path/india-latest.osm.pbf
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

import osmium


KEEP_KEYS = {"amenity", "shop", "craft", "tourism", "office", "name", "brand", "cuisine", "opening_hours"}
BUSINESS_KEYS = {"amenity", "shop", "craft", "tourism"}


class PoiHandler(osmium.SimpleHandler):
    def __init__(self, database: sqlite3.Connection) -> None:
        super().__init__()
        self.database = database
        self.total = 0

    def node(self, node: osmium.osm.Node) -> None:
        if not node.location.valid():
            return
        tags = {key: value for key, value in node.tags if key in KEEP_KEYS}
        if not any(key in tags for key in BUSINESS_KEYS):
            return
        # Retain potential business features only. This avoids indexing every
        # amenity such as benches, waste baskets, or drinking-water points.
        if tags.get("amenity") in {"bench", "waste_basket", "drinking_water", "toilets", "parking", "bicycle_parking"}:
            return
        cursor = self.database.execute(
            "INSERT INTO osm_poi(osm_type, osm_id, name, latitude, longitude, tags) VALUES (?, ?, ?, ?, ?, ?)",
            ("node", node.id, tags.get("name"), node.location.lat, node.location.lon, json.dumps(tags, ensure_ascii=False)),
        )
        self.database.execute(
            "INSERT INTO poi_rtree(id, min_lat, max_lat, min_lon, max_lon) VALUES (?, ?, ?, ?, ?)",
            (cursor.lastrowid, node.location.lat, node.location.lat, node.location.lon, node.location.lon),
        )
        self.total += 1
        if self.total % 50000 == 0:
            self.database.commit()
            print(f"Indexed {self.total:,} business POIs", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pbf", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "osm_competitors.sqlite")
    args = parser.parse_args()
    if not args.pbf.is_file():
        raise SystemExit(f"PBF source not found: {args.pbf}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        args.output.unlink()
    database = sqlite3.connect(args.output)
    database.executescript(
        "CREATE TABLE osm_poi (osm_type TEXT NOT NULL, osm_id INTEGER NOT NULL, name TEXT, latitude REAL NOT NULL, longitude REAL NOT NULL, tags TEXT NOT NULL);"
        "CREATE INDEX idx_osm_poi_identity ON osm_poi(osm_type, osm_id);"
        "CREATE VIRTUAL TABLE poi_rtree USING rtree(id, min_lat, max_lat, min_lon, max_lon);"
        "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);"
    )
    handler = PoiHandler(database)
    handler.apply_file(str(args.pbf), locations=False)
    database.execute("INSERT INTO metadata(key, value) VALUES (?, ?)", ("source", str(args.pbf.name)))
    database.execute("INSERT INTO metadata(key, value) VALUES (?, datetime('now'))", ("indexed_at",))
    database.commit()
    database.close()
    print(f"Indexed {handler.total:,} point features into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
