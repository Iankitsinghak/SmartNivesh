import json
from typing import List, Dict, Any
from app.schemas.place import Place
from app.schemas.business import BusinessCategory
from app.schemas.market import POIResult
from app.utils.geo import calculate_distance

def get_all_places() -> List[Place]:
    places = []
    try:
        with open("data/places.json", "r") as f:
            data = json.load(f)
            for item in data:
                places.append(Place(**item))
    except Exception:
        pass
    return places

def analyze_pois(lat: float, lon: float, category: BusinessCategory, max_radius: float = 10.0) -> POIResult:
    all_places = get_all_places()
    
    result = POIResult(within_2km={}, within_5km={}, within_10km={}, relevant_signals=[])
    
    for place in all_places:
        dist = calculate_distance(lat, lon, place.latitude, place.longitude)
        if dist > max_radius:
            continue
            
        # Add to radius breakdown
        radius_band = None
        if dist <= 2.0:
            radius_band = result.within_2km
        elif dist <= 5.0:
            radius_band = result.within_5km
        else:
            radius_band = result.within_10km
            
        radius_band[place.poi_type] = radius_band.get(place.poi_type, 0) + 1
        
        # Check relevance
        if place.poi_type in category.relevant_poi_types:
            relevance = "HIGH" if dist <= 2.0 else "MEDIUM" if dist <= 5.0 else "LOW"
            result.relevant_signals.append({
                "type": place.poi_type,
                "name": place.name,
                "distance": round(dist, 2),
                "relevance": relevance
            })
            
    return result
