import json
from typing import Optional
from app.schemas.location import Location

def get_location(location_id: str) -> Optional[Location]:
    """
    Mock resolver using local seeded data. 
    In production this would query PostgreSQL.
    """
    try:
        with open("data/locations.json", "r") as f:
            locations = json.load(f)
            for loc in locations:
                if loc["location_id"] == location_id:
                    return Location(**loc)
    except Exception:
        pass
    return None
