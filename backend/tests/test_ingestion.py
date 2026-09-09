import pytest
from app.services.ingestion.normalizer import (
    normalize_poi_category,
    normalize_business_category,
    is_duplicate,
    extract_lat_lon,
    generate_id
)

def test_normalize_poi_category():
    assert normalize_poi_category({"amenity": "school"}) == "EDUCATION"
    assert normalize_poi_category({"amenity": "hospital"}) == "HEALTHCARE"
    assert normalize_poi_category({"amenity": "bank"}) == "FINANCE"
    assert normalize_poi_category({"historic": "monument"}) == "TOURISM"
    assert normalize_poi_category({"amenity": "unknown_thing"}) == "OTHER_POI"

def test_normalize_business_category():
    assert normalize_business_category({"amenity": "restaurant"}) == "FOOD_AND_BEVERAGE"
    assert normalize_business_category({"shop": "supermarket"}) == "GROCERY"
    assert normalize_business_category({"amenity": "pharmacy"}) == "PHARMACY"
    assert normalize_business_category({"shop": "unknown_shop"}) == "RETAIL_OTHER"
    assert normalize_business_category({"office": "lawyer"}) == "OFFICE"
    assert normalize_business_category({"amenity": "library"}) == "OTHER_BUSINESS"

def test_is_duplicate():
    # Same name, very close
    assert is_duplicate(28.7041, 77.1025, 28.70411, 77.10251, "Ramu Kirana", "ramu kirana") == True
    
    # Same name, far away
    assert is_duplicate(28.7041, 77.1025, 28.8041, 77.2025, "Ramu Kirana", "Ramu Kirana") == False
    
    # Different name, close
    assert is_duplicate(28.7041, 77.1025, 28.7041, 77.1025, "Ramu Kirana", "Shyam Kirana") == False

def test_extract_lat_lon():
    node = {"type": "node", "lat": 28.1, "lon": 77.1}
    assert extract_lat_lon(node) == (28.1, 77.1)
    
    way = {"type": "way", "center": {"lat": 28.2, "lon": 77.2}}
    assert extract_lat_lon(way) == (28.2, 77.2)

def test_generate_id():
    assert generate_id("POI", 12345) == "POI-12345"
