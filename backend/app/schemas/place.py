from pydantic import BaseModel

class Place(BaseModel):
    place_id: str
    name: str
    poi_type: str
    latitude: float
    longitude: float
