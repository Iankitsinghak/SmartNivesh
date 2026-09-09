import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.place import PlaceRecord
from app.core.enums import Provenance
from app.services.ingestion.osm_client import OSMClient
from app.services.ingestion.normalizer import normalize_poi_category, extract_lat_lon, generate_id, is_duplicate

def ingest_pois_from_osm(lat: float, lon: float, radius: float = 5000):
    client = OSMClient()
    print(f"Fetching POIs from OSM around {lat}, {lon} within {radius}m...")
    elements = client.fetch_pois_in_radius(lat, lon, radius)
    print(f"Found {len(elements)} raw elements.")
    
    db = SessionLocal()
    inserted = 0
    updated = 0
    skipped = 0
    
    try:
        # Load existing POIs in DB for deduplication
        existing_records = db.query(PlaceRecord).all()
        
        for element in elements:
            tags = element.get("tags", {})
            name = tags.get("name", "Unknown POI")
            
            # Normalization
            category = normalize_poi_category(tags)
            if category == "OTHER_POI" and name == "Unknown POI":
                # Skip unidentifiable places
                skipped += 1
                continue
                
            el_lat, el_lon = extract_lat_lon(element)
            if el_lat == 0.0 and el_lon == 0.0:
                skipped += 1
                continue
                
            place_id = generate_id("POI-OSM", element["id"])
            
            # Deduplication Check
            duplicate = False
            for ex in existing_records:
                if is_duplicate(el_lat, el_lon, ex.latitude, ex.longitude, name, ex.name):
                    duplicate = True
                    break
            
            if duplicate:
                skipped += 1
                continue
                
            existing = db.query(PlaceRecord).filter(PlaceRecord.place_id == place_id).first()
            if existing:
                existing.category = category
                existing.name = name
                existing.latitude = el_lat
                existing.longitude = el_lon
                existing.dataset_date = datetime.now().isoformat()
                updated += 1
            else:
                new_poi = PlaceRecord(
                    place_id=place_id,
                    category=category,
                    name=name,
                    latitude=el_lat,
                    longitude=el_lon,
                    source_id="osm",
                    dataset_date=datetime.now().isoformat(),
                    provenance=Provenance.ESTIMATED
                )
                db.add(new_poi)
                # update our in-memory cache to catch duplicates in the same batch
                existing_records.append(new_poi)
                inserted += 1
                
        db.commit()
        print(f"POIs Ingestion: {inserted} inserted, {updated} updated, {skipped} skipped/duplicates.")
    except Exception as e:
        db.rollback()
        print(f"Error ingesting POIs: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Example coordinates for Model Town, Delhi
    ingest_pois_from_osm(28.7041, 77.1025)
