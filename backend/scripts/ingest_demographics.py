import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.demographic import DemographicRecord
from app.core.enums import Provenance

def ingest_demographics():
    db = SessionLocal()
    try:
        with open("data/demographics.json", "r") as f:
            data = json.load(f)
            
        inserted = 0
        updated = 0
        
        for item in data:
            location_id = item.get("location_id")
            for key, value in item.items():
                if key == "location_id":
                    continue
                    
                indicator = key
                unit = "count"
                if "rate" in key:
                    unit = "ratio"
                
                existing = db.query(DemographicRecord).filter(
                    DemographicRecord.location_id == location_id,
                    DemographicRecord.indicator == indicator
                ).first()
                
                if existing:
                    existing.value = float(value)
                    existing.unit = unit
                    updated += 1
                else:
                    new_demo = DemographicRecord(
                        location_id=location_id,
                        indicator=indicator,
                        value=float(value),
                        unit=unit,
                        geographic_scope="VILLAGE",
                        source_id="census",
                        dataset_date="2011",
                        provenance=Provenance.VERIFIED
                    )
                    db.add(new_demo)
                    inserted += 1
                
        db.commit()
        print(f"Demographics Ingestion: {inserted} inserted, {updated} updated.")
    except Exception as e:
        db.rollback()
        print(f"Error ingesting demographics: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    ingest_demographics()
