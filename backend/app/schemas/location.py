from pydantic import BaseModel
from typing import Optional

class LocationHierarchy(BaseModel):
    country: str = "India"
    state: str
    district: str
    block: Optional[str] = None
    village_town: str

class Location(BaseModel):
    location_id: str
    latitude: float
    longitude: float
    hierarchy: LocationHierarchy
