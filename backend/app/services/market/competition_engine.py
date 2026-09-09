import json
from typing import List
from app.schemas.business import Business, BusinessCategory
from app.utils.geo import calculate_distance, distance_decay
from app.utils.provenance import ConfidenceLevel
from app.schemas.market import CompetitionResult
from app.utils.normalization import get_generic_level, clamp_score

from app.core.database import SessionLocal
from app.models.business import BusinessRecord

def get_all_businesses() -> List[Business]:
    db = SessionLocal()
    businesses = []
    try:
        # Load from the new PostgreSQL/SQLite DB
        records = db.query(BusinessRecord).all()
        for r in records:
            businesses.append(Business(
                business_id=r.business_id,
                category_id=r.category,
                name=r.name,
                latitude=r.latitude,
                longitude=r.longitude,
                source_id=r.source_id,
                dataset_date=r.dataset_date,
                provenance=r.provenance
            ))
    except Exception:
        pass
    finally:
        db.close()
    return businesses

def analyze_competition(lat: float, lon: float, category: BusinessCategory, radius_km: float = 10.0) -> CompetitionResult:
    all_businesses = get_all_businesses()
    
    mapped_competitors = 0
    near_competitors = 0
    weighted_score = 0.0
    
    for b in all_businesses:
        if b.category_id in category.competitor_categories:
            dist = calculate_distance(lat, lon, b.latitude, b.longitude)
            if dist <= radius_km:
                mapped_competitors += 1
                if dist <= 2.0:
                    near_competitors += 1
                
                # Use bounded distance decay for impact
                weighted_score += distance_decay(dist, scale_factor=2.0)
                
    # Normalize score based on a presumed saturation point, say 5 close competitors = 100% competition
    # This is a deterministic rule.
    raw_competition_score = (weighted_score / 5.0) * 100
    final_score = clamp_score(raw_competition_score)
    
    level = get_generic_level(final_score)
    
    return CompetitionResult(
        mapped_competitors=mapped_competitors,
        near_competitors=near_competitors,
        competition_score=round(final_score, 2),
        competition_level=level,
        confidence=ConfidenceLevel.MEDIUM if all_businesses else ConfidenceLevel.LOW
    )

