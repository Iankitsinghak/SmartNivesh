import uuid
from typing import Dict, Any, Tuple
from app.utils.geo import calculate_distance

def normalize_poi_category(tags: Dict[str, str]) -> str:
    amenity = tags.get("amenity")
    if amenity in ["school", "college", "university", "kindergarten"]:
        return "EDUCATION"
    if amenity in ["hospital", "clinic", "doctors", "pharmacy"]:
        return "HEALTHCARE"
    if amenity in ["bank", "atm"]:
        return "FINANCE"
    if amenity in ["place_of_worship"]:
        return "RELIGIOUS"
    if tags.get("historic") or tags.get("tourism"):
        return "TOURISM"
    if tags.get("public_transport") or amenity in ["bus_station", "taxi"]:
        return "TRANSPORT"
    
    return "OTHER_POI"

def normalize_business_category(tags: Dict[str, str]) -> str:
    shop = tags.get("shop")
    amenity = tags.get("amenity")
    office = tags.get("office")
    
    if amenity in ["restaurant", "cafe", "fast_food", "bar", "pub"]:
        return "FOOD_AND_BEVERAGE"
    if shop in ["supermarket", "convenience", "grocery", "greengrocer"]:
        return "GROCERY"
    if amenity == "pharmacy":
        return "PHARMACY"
    if shop in ["clothes", "shoes", "tailor", "boutique"]:
        return "APPAREL"
    if shop in ["hairdresser", "beauty", "salon"]:
        return "SALON"
    if shop in ["electronics", "mobile_phone", "computer"]:
        return "ELECTRONICS"
    if shop == "bakery":
        return "BAKERY"
    if shop in ["car_repair", "motorcycle_repair", "garage"]:
        return "GARAGE"
    
    if shop:
        return "RETAIL_OTHER"
    if office:
        return "OFFICE"
        
    return "OTHER_BUSINESS"

def is_duplicate(lat1: float, lon1: float, lat2: float, lon2: float, name1: str, name2: str) -> bool:
    # Very basic deduplication: same name and within 50 meters
    if not name1 or not name2:
        return False
    if name1.lower().strip() == name2.lower().strip():
        dist = calculate_distance(lat1, lon1, lat2, lon2)
        if dist < 0.05: # 50 meters
            return True
    return False

def extract_lat_lon(element: Dict[str, Any]) -> Tuple[float, float]:
    if element["type"] == "node":
        return element.get("lat", 0.0), element.get("lon", 0.0)
    elif element["type"] in ["way", "relation"] and "center" in element:
        return element["center"].get("lat", 0.0), element["center"].get("lon", 0.0)
    return 0.0, 0.0

def generate_id(prefix: str, osm_id: int) -> str:
    return f"{prefix}-{osm_id}"
