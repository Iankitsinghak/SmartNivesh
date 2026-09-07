from typing import List
from app.schemas.business import BusinessCategory
from app.schemas.market import BusinessActivityResult
from app.utils.geo import calculate_distance, distance_decay
from app.utils.normalization import get_generic_level, clamp_score
from app.services.market.competition_engine import get_all_businesses

def analyze_business_activity(lat: float, lon: float, category: BusinessCategory, radius_km: float = 10.0) -> BusinessActivityResult:
    all_businesses = get_all_businesses()
    
    total_density = 0.0
    complementary_count = 0
    supplier_count = 0
    relevant_count = 0
    
    for b in all_businesses:
        dist = calculate_distance(lat, lon, b.latitude, b.longitude)
        if dist <= radius_km:
            total_density += distance_decay(dist, scale_factor=3.0)
            
            if b.category_id in category.complementary_categories:
                complementary_count += 1
                relevant_count += 1
                
            if b.category_id in category.supplier_categories:
                supplier_count += 1
                relevant_count += 1

    # Base density plus bonus for relevant complementary/suppliers
    activity_score = clamp_score((total_density * 5.0) + (relevant_count * 10.0))
    
    return BusinessActivityResult(
        commercial_activity_score=round(activity_score, 2),
        business_density=round(total_density, 2),
        relevant_business_count=relevant_count,
        complementary_business_count=complementary_count,
        supplier_presence=supplier_count,
        market_activity_level=get_generic_level(activity_score)
    )
