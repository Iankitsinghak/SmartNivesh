import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.location import LocationRecord

def ingest_locations():
    db = SessionLocal()
    try:
        with open("data/locations.json", "r") as f:
            data = json.load(f)
            
        inserted = 0
        updated = 0
        
        for item in data:
            location_id = item.get("location_id")
            existing = db.query(LocationRecord).filter(LocationRecord.location_id == location_id).first()
            
            if existing:
                existing.latitude = item.get("latitude")
                existing.longitude = item.get("longitude")
                existing.hierarchy = item.get("hierarchy")
                updated += 1
            else:
                new_loc = LocationRecord(
                    location_id=location_id,
                    latitude=item.get("latitude"),
                    longitude=item.get("longitude"),
                    hierarchy=item.get("hierarchy")
                )
                db.add(new_loc)
                inserted += 1
                
        db.commit()
        print(f"Locations Ingestion: {inserted} inserted, {updated} updated.")
    except Exception as e:
        db.rollback()
        print(f"Error ingesting locations: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    ingest_locations()
