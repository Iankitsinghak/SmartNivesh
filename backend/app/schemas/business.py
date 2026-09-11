from pydantic import BaseModel
from typing import Dict, List, Optional

class DemographicSegment(BaseModel):
    segment: str
    weight: float

class BusinessCategory(BaseModel):
    category_id: str
    name: str
    description: Optional[str] = None
    capital_min: float = 0.0
    capital_max: float = 0.0
    target_segments: List[DemographicSegment] = []
    relevant_poi_types: List[str] = []
    competitor_categories: List[str] = []
    complementary_categories: List[str] = []
    supplier_categories: List[str] = []
    seasonality_profile: dict = {}
    distribution_profile: dict = {}
    # Live OpenStreetMap tags that identify businesses comparable to this category.
    # This is category configuration, not a source of business records.
    osm_competitor_tags: List[Dict[str, str]] = []

class Business(BaseModel):
    business_id: str
    name: str
    category_id: str
    latitude: float
    longitude: float
