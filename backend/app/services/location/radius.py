from typing import List, Dict, Any
from app.utils.geo import calculate_distance
from app.schemas.location import Location

def group_by_radius(target_lat: float, target_lon: float, entities: List[Any]) -> Dict[str, List[Any]]:
    """
    Groups entities (places or businesses) into 0-2km, 2-5km, and 5-10km bands.
    Entities should have 'latitude' and 'longitude' attributes.
    """
    bands = {
        "0_2_km": [],
        "2_5_km": [],
        "5_10_km": []
    }

    for entity in entities:
        dist = calculate_distance(target_lat, target_lon, entity.latitude, entity.longitude)
        
        # We attach the calculated distance dynamically for easier processing down the line
        entity_with_dist = {"entity": entity, "distance": dist}
        
        if dist <= 2.0:
            bands["0_2_km"].append(entity_with_dist)
        elif dist <= 5.0:
            bands["2_5_km"].append(entity_with_dist)
        elif dist <= 10.0:
            bands["5_10_km"].append(entity_with_dist)
            
    return bands
